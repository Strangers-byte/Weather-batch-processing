{{
  config(
    materialized = 'table',
    )
}}

WITH weather AS (
    SELECT
        payload.latitude AS latitude,
        payload.longitude AS longitude,
        UNNEST(payload.hourly.time) AS observation_time,
        UNNEST(payload.hourly.temperature_2m) AS temperature_c,
        UNNEST(payload.hourly.relative_humidity_2m) AS humidity_pct,
        UNNEST(payload.hourly.wind_speed_10m) AS wind_speed_kmh,
        UNNEST(payload.hourly.weather_code) AS weather_code
    FROM {{ ref('weather') }}
),

city_seed AS (
    SELECT city_id, latitude, longitude
    FROM {{ ref('city_list') }}
)

SELECT
    c.city_id,
    w.observation_time::timestamp AS observation_time,
    w.temperature_c::double AS temperature_c,
    w.humidity_pct::double AS humidity_pct,
    w.wind_speed_kmh::double AS wind_speed_kmh,
    w.weather_code::integer AS weather_code,
    current_timestamp AS silver_loaded_at
FROM weather w
JOIN city_seed c
    ON round(w.latitude, 1) = round(c.latitude, 1)
    AND round(w.longitude, 1) = round(c.longitude, 1)