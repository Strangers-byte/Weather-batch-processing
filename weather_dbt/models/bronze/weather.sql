{{
  config(
    materialized = 'table',
    )
}}

SELECT
    *,
    current_timestamp AS bronze_loaded_at
FROM read_json_auto('D:/MyData/Ahmads/Projects/DBT/Weather/data/raw/weather/*.json')