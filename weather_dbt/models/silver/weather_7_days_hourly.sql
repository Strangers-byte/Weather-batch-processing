{{
  config(
    materialized = 'view',
    )
}}

WITH weather AS (
    SELECT
        latitude,
        longitude,
        UNNEST(
            list_zip(
                hourly.time,
                hourly.temperature_2m,
                hourly.relative_humidity_2m,
                hourly.wind_speed_10m,
                hourly.weather_code
            )
        ) AS hourly_row
    FROM {{ ref('weather') }}
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
    w.hourly_row[1]::timestamp AS observation_time,
    w.hourly_row[2]::double AS temperature_c,
    w.hourly_row[3]::double AS humidity_pct,
    w.hourly_row[4]::double AS wind_speed_kmh,
    w.hourly_row[5]::integer AS weather_code,
    current_timestamp AS silver_loaded_at
FROM weather w
JOIN city_seed c
    ON round(w.latitude, 1) = round(c.latitude, 1)
    AND round(w.longitude, 1) = round(c.longitude, 1)