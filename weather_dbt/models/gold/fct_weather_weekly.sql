{{ config(materialized='table') }}

WITH weather_hourly AS (
    SELECT * FROM {{ ref('weather_7_days_hourly') }}
),

aq_hourly AS (
    SELECT * FROM {{ ref('air_quality_7_days_hourly') }}
),

bounds AS (
    SELECT CAST(MIN(observation_time) AS DATE) AS window_start
    FROM weather_hourly
),

weekly_agg AS (
    SELECT
        wh.city_id,
        b.window_start AS week_start,
        MIN(wh.temperature_c) AS weekly_min_temp_c,
        MAX(wh.temperature_c) AS weekly_max_temp_c,
        AVG(wh.temperature_c) AS weekly_avg_temp_c,
        MAX(wh.wind_speed_kmh) AS weekly_max_wind_speed_kmh,
        MAX(aqh.european_aqi) AS weekly_max_european_aqi,
        COUNT(wh.observation_time) AS hour_count,
        COUNT(aqh.observation_time) AS aq_hour_count

    FROM weather_hourly wh
    CROSS JOIN bounds b
    LEFT JOIN aq_hourly aqh 
        ON aqh.city_id = wh.city_id 
        AND aqh.observation_time = wh.observation_time
    
    GROUP BY wh.city_id, b.window_start 
)

SELECT
    city_id,
    week_start,
    weekly_min_temp_c,
    weekly_max_temp_c,
    weekly_avg_temp_c,
    weekly_max_wind_speed_kmh,
    weekly_max_european_aqi,
    hour_count,
    aq_hour_count,

    RANK() OVER (PARTITION BY week_start ORDER BY weekly_avg_temp_c DESC) AS rank_by_avg_temp,

    CURRENT_TIMESTAMP AS computed_at

FROM weekly_agg