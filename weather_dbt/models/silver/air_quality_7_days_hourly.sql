{{
  config(
    materialized = 'table',
    )
}}

WITH air_quality AS (
    SELECT
        city_id,
        UNNEST(payload.hourly.time) AS observation_time,
        UNNEST(payload.hourly.european_aqi) AS european_aqi,
        UNNEST(payload.hourly.us_aqi) AS us_aqi,
        UNNEST(payload.hourly.pm10) AS pm10,
        UNNEST(payload.hourly.pm2_5) AS pm2_5
    FROM {{ ref('air_quality') }}
)

SELECT
    city_id,
    observation_time::timestamp AS observation_time,
    european_aqi::integer AS european_aqi,
    us_aqi::integer AS us_aqi,
    pm10::double AS pm10,
    pm2_5::double AS pm2_5,
    current_timestamp AS silver_loaded_at
FROM air_quality