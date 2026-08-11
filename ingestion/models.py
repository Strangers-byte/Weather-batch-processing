from pydantic import BaseModel, Field, validator
from typing import List, Optional

class WeatherHourlyData(BaseModel):
    time: List[str]
    temperature_2m: List[Optional[float]]  
    relative_humidity_2m: List[Optional[int]]
    wind_speed_10m: List[Optional[float]]
    weather_code: List[Optional[int]]

class AirQualityHourlyData(BaseModel):
    time: List[str]
    european_aqi: List[Optional[int]]
    us_aqi: List[Optional[int]]
    pm10: List[Optional[float]]             
    pm2_5: List[Optional[float]]  

class OpenMeteoWeatherResponse(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    generationtime_ms: float
    utc_offset_seconds: int
    timezone: str
    timezone_abbreviation: str
    elevation: float
    hourly: WeatherHourlyData

    @validator('hourly')
    def arrays_same_length(cls, v: WeatherHourlyData):
        lengths = {len(v.time), len(v.temperature_2m), len(v.relative_humidity_2m), len(v.wind_speed_10m), len(v.weather_code)}
        if len(lengths) != 1:
            raise ValueError(f"Weather hourly arrays have mismatched lengths: {lengths}")
        return v

class OpenMeteoAirQualityResponse(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    generationtime_ms: float
    utc_offset_seconds: int
    timezone: str
    timezone_abbreviation: str
    elevation: float
    hourly: AirQualityHourlyData
    
    @validator('hourly')
    def arrays_same_length(cls, v: AirQualityHourlyData):
        lengths = {len(v.time), len(v.european_aqi), len(v.us_aqi), len(v.pm10), len(v.pm2_5)}
        if len(lengths) != 1:
            raise ValueError(f"Air quality hourly arrays have mismatched lengths: {lengths}")
        return v