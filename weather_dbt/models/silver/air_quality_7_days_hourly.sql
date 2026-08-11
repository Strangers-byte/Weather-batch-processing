{{
  config(
    materialized = 'table',
    )
}}

WITH air_quality AS (
    SELECT
        payload.latitude,
        payload.longitude,
        UNNEST(payload.hourly.time) AS observation_time,
        UNNEST(payload.hourly.european_aqi) AS european_aqi,
        UNNEST(payload.hourly.us_aqi) AS us_aqi,
        UNNEST(payload.hourly.pm10) AS pm10,
        UNNEST(payload.hourly.pm2_5) AS pm2_5
    FROM {{ ref('air_quality') }}
),

city_seed AS (
    SELECT
        city_id,
        latitude,
        longitude
    FROM {{ ref('city_list') }}
)

SELECT
    c.city_id,
    aq.observation_time::timestamp AS observation_time,
    aq.european_aqi::integer AS european_aqi,
    aq.us_aqi::integer AS us_aqi,
    aq.pm10::double AS pm10,
    aq.pm2_5::double AS pm2_5,
    current_timestamp AS silver_loaded_at
FROM air_quality aq
JOIN city_seed c
    ON round(aq.latitude, 1) = round(c.latitude, 1)
    AND round(aq.longitude, 1) = round(c.longitude, 1)