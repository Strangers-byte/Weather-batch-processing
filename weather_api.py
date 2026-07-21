import requests
import logging_config
import logging
import os
import json
import time

from datetime import datetime, timezone


logger = logging.getLogger(__name__)

WEATHER_URL='https://api.open-meteo.com/v1/forecast'
AIR_QUALITY_URL="https://air-quality-api.open-meteo.com/v1/air-quality"


class WeatherAPIClient:
    def fetch_current_weather(self, city: dict):
        try:
            params = {
                "latitude": city['lat'], 
                "longitude": city['lon'], 
                "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code"
            }
            response = requests.get(WEATHER_URL, params=params, timeout=30)

            if response.status_code != 200:
                logger.error('Weather API error: %s %s', response.status_code, response.text)
            return response.json() 
        except Exception as e:
            logger.error("Weather API error: %s" ,e)
        

    def fetch_air_quality(self, city: dict):
        try:
            params={
            "latitude": city['lat'], 
            "longitude": city['lon'], 
            "hourly": "european_aqi,us_aqi,pm10,pm2_5"
            }
            response = requests.get(AIR_QUALITY_URL, params=params, timeout=30)

            if response.status_code != 200:
                logger.error('Air quality API error: %s %s', response.status_code, response.text)
            return response.json()
        except Exception as e:
            logger.error("Air quality API error: %s" ,e)
        

    def city_data_for_API(self, GERMAN_CITIES: list)-> list:
        for i, city in enumerate(GERMAN_CITIES):
            try:
                logger.info("Processing city index %d: %s", i, city['city_name'])
                weather_data = self.fetch_current_weather(city)
                time.sleep(1.2) #Safe margin under 50 calls/min
                air_quality_data = self.fetch_air_quality(city)
                time.sleep(1.2) #Safe margin under 50 calls/min
                self.save_raw_json("weather", weather_data, city['city_id'])
                self.save_raw_json("air_quality", air_quality_data, city['city_id'])

            except Exception as e:
                logger.error("Failed to fetch weather for %s: %s", city['city_name'], e)
                # print(e)

    def save_raw_json(self, data_type:str, data:dict, city:str):
        dir_path = f"data/raw/{data_type}"
        os.makedirs(dir_path, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = f"{city}_{timestamp}.json"
        filepath = os.path.join(dir_path, filename)
        with open(filepath, "w") as f:
            json.dump(data, f)
        logger.info(f"Saved {data_type} for {city} to {filepath}")

