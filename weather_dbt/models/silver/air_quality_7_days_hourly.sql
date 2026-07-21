{{
  config(
    materialized = 'view',
    )
}}

WITH air_quality AS (
    SELECT
        latitude,
        longitude,
        UNNEST(
            list_zip(
                hourly.time,
                hourly.european_aqi,
                hourly.us_aqi,
                hourly.pm10,
                hourly.pm2_5
            )
        ) AS hourly_row
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
    aq.hourly_row[1]::timestamp AS observation_time,
    aq.hourly_row[2]::integer AS european_aqi,
    aq.hourly_row[3]::integer AS us_aqi,
    aq.hourly_row[4]::double AS pm10,
    aq.hourly_row[5]::double AS pm2_5,
    current_timestamp AS silver_loaded_at
FROM air_quality aq
JOIN city_seed c
    ON round(aq.latitude, 1) = round(c.latitude, 1)
    AND round(aq.longitude, 1) = round(c.longitude, 1)