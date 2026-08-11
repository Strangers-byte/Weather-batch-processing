import logging_config
import logging
import json

from datetime import datetime, timezone, timedelta
from pathlib import Path
from pydantic import ValidationError

from models import OpenMeteoWeatherResponse, OpenMeteoAirQualityResponse
from resilient_client import ResilientOpenMeteoClient, CircuitOpenError

logger = logging.getLogger(__name__)

WEATHER_URL='https://api.open-meteo.com/v1/forecast'
AIR_QUALITY_URL="https://air-quality-api.open-meteo.com/v1/air-quality"

TODAY = datetime.now(timezone.utc).date()
START_DATE = TODAY.strftime("%Y-%m-%d")
END_DATE = (TODAY + timedelta(days=6)).strftime("%Y-%m-%d")



class WeatherAPIClient:
    def __init__(self):
        self.client = ResilientOpenMeteoClient(
            min_interval_seconds=1.2,
            max_retries=3,
            failure_threshold=5,
            cooldown_seconds=60
        )


    def fetch_current_weather(self, city: dict):
        params = {
            "latitude": city['lat'], 
            "longitude": city['lon'],
            "start_date": START_DATE,
            "end_date": END_DATE, 
            "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code"
            }
        return self.client.get(WEATHER_URL, params=params)
    

    def fetch_air_quality(self, city: dict):
        params={
            "latitude": city['lat'], 
            "longitude": city['lon'],
            "start_date": START_DATE,
            "end_date": END_DATE, 
            "hourly": "european_aqi,us_aqi,pm10,pm2_5"
            }
        return self.client.get(AIR_QUALITY_URL, params=params)
        

    def run(self, cities: list) -> list:
        """
        Fetch and validate data for all cities.
        Returns list of failed (city, endpoint, reason) tuples.
        """
        failed = []

        for i, city in enumerate(cities):
            logger.info("Processing city %d/%d: %s", i + 1, len(cities), city['city_name'])

            try:
                raw = self.fetch_current_weather(city)
                validated = OpenMeteoWeatherResponse(**raw)
                logger.debug("Validated weather for %s: %d hourly records",
                             city['city_name'], len(validated.hourly.time))
                self.save_raw_json("weather", raw, city['city_id'])

            except CircuitOpenError:
                logger.warning("Circuit open — skipping weather for %s", city['city_name'])
                failed.append((city['city_name'], 'weather', 'circuit_open'))

            except ValidationError as e:
                logger.error("Weather validation failed for %s: %s", city['city_name'], e)
                failed.append((city['city_name'], 'weather', f'validation_error: {e}'))

            except Exception as e:
                logger.error("Weather fetch failed for %s: %s", city['city_name'], e)
                failed.append((city['city_name'], 'weather', str(e)))



            try:
                raw = self.fetch_air_quality(city)
                validated = OpenMeteoAirQualityResponse(**raw)
                logger.debug("Validated air quality for %s: %d hourly records",
                             city['city_name'], len(validated.hourly.time))
                self.save_raw_json("air_quality", raw, city['city_id'])

            except CircuitOpenError:
                logger.warning("Circuit open — skipping air quality for %s", city['city_name'])
                failed.append((city['city_name'], 'air_quality', 'circuit_open'))

            except ValidationError as e:
                logger.error("Air quality validation failed for %s: %s", city['city_name'], e)
                failed.append((city['city_name'], 'air_quality', f'validation_error: {e}'))

            except Exception as e:
                logger.error("Air quality fetch failed for %s: %s", city['city_name'], e)
                failed.append((city['city_name'], 'air_quality', str(e)))

        if failed:
            logger.warning("Completed with %d failed fetches: %s", len(failed), failed)

        return failed

    def save_raw_json(self, data_type: str, data: dict, city_id: str):
        """
        Idempotent save: filename is deterministic per city + date range.
        Overwrites existing file to ensure freshness.
        """
        dir_path = Path(f"data/raw/{data_type}")
        dir_path.mkdir(parents=True, exist_ok=True)


        filename = f"{city_id}_{START_DATE}_{END_DATE}.json"
        filepath = dir_path / filename

        record = {
            "city_id": city_id,
            "start_date": START_DATE,
            "end_date": END_DATE,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "api_version": "v1",
            "payload": data,
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2)

        logger.info("Saved %s for %s → %s", data_type, city_id, filepath)