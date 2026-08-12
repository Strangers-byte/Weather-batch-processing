{{
  config(
    materialized = 'table',
    )
}}

WITH weather AS (
    SELECT
        city_id,
        UNNEST(payload.hourly.time) AS observation_time,
        UNNEST(payload.hourly.temperature_2m) AS temperature_c,
        UNNEST(payload.hourly.relative_humidity_2m) AS humidity_pct,
        UNNEST(payload.hourly.wind_speed_10m) AS wind_speed_kmh,
        UNNEST(payload.hourly.weather_code) AS weather_code
    FROM {{ ref('weather') }}
)

SELECT
    city_id,
    observation_time::timestamp AS observation_time,
    temperature_c::double AS temperature_c,
    humidity_pct::double AS humidity_pct,
    wind_speed_kmh::double AS wind_speed_kmh,
    weather_code::integer AS weather_code,
    current_timestamp AS silver_loaded_at
FROM weather