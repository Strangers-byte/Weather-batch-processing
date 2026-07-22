# Weather Insights Pipeline

A data pipeline that fetches hourly weather and air quality data for 10 German cities from the Open‑Meteo API, processes it with dbt + DuckDB. 

## Tech Stack
- **Extraction:** Python (requests) with rate limiting & retries
- **Storage & Query:** DuckDB
- **Transformation:** dbt (data build tool)

## Data

- **API:** Open‑Meteo (free, no key required)
- **Endpoints:** Forecast (`/v1/forecast`) and Air Quality (`/v1/air-quality`)
- **Cities:** 10 German cities (Berlin, Hamburg, Munich, …)

## Pipeline Layers

- **Bronze:** Raw JSON files (immutable)
- **Silver:** Cleaned hourly time series with `city_id`

## Key Features

- **Rate limiting** with exponential backoff