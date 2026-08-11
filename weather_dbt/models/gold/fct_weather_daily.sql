{{ config(materialized='table') }}

WITH weather_hourly AS (
    SELECT * FROM {{ ref('weather_7_days_hourly') }}
),

aq_hourly AS (
    SELECT * FROM {{ ref('air_quality_7_days_hourly') }}
)

SELECT
    wh.city_id,
    CAST(wh.observation_time AS DATE) AS date_day,

    MIN(wh.temperature_c) AS min_temp_c,
    MAX(wh.temperature_c) AS max_temp_c,
    AVG(wh.temperature_c) AS avg_temp_c,

    AVG(wh.humidity_pct) AS avg_humidity_pct,
    MAX(wh.wind_speed_kmh) AS max_wind_speed_kmh,

    MIN(aqh.european_aqi) AS min_european_aqi,
    MAX(aqh.european_aqi) AS max_european_aqi,
    AVG(aqh.european_aqi) AS avg_european_aqi,

    COUNT(wh.observation_time) AS hour_count, 
    COUNT(aqh.observation_time) AS aq_hour_count,  

    CURRENT_TIMESTAMP AS computed_at

FROM weather_hourly wh
LEFT JOIN aq_hourly aqh 
    ON aqh.city_id = wh.city_id 
    AND aqh.observation_time = wh.observation_time

GROUP BY wh.city_id, CAST(wh.observation_time AS DATE)