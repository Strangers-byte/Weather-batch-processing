{{ config(materialized='table') }}

SELECT
    city_id,
    city_name,
    country,
    latitude,
    longitude
FROM {{ ref('city_list') }}