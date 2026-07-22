# Weather Insights Pipeline

A data pipeline that fetches hourly weather and air quality data for 10 German cities from the Open‑Meteo API, processes it with dbt + DuckDB, and models it in a star schema with a Type 2 Slowly Changing Dimension.

## Tech Stack

- **Orchestration:** Apache Airflow
- **Extraction:** Python (requests) with rate limiting & retries
- **Storage & Query:** DuckDB
- **Transformation:** dbt (data build tool)
- **Containerization:** Docker Compose

## Data

- **API:** Open‑Meteo (free, no key required)
- **Endpoints:** Forecast (`/v1/forecast`) and Air Quality (`/v1/air-quality`)
- **Cities:** 10 German cities (Berlin, Hamburg, Munich, …)

## Pipeline Layers

- **Bronze:** Raw JSON files (immutable)
- **Silver:** Cleaned hourly time series with `city_id`
- **Gold:** Star schema
  - `dim_city` – Type 2 SCD (tracks name/coordinate changes)
  - `fct_weather_hourly` and `fct_air_quality_hourly` – fact tables

## Key Features

- **Rate limiting** with exponential backoff
- **SCD Type 2** on city dimension (dbt snapshot)
- **Incremental loads** in fact tables
- **Data quality tests** (dbt tests)

## Quick Start

```bash
docker compose up -d
dbt seed
dbt run
dbt snapshot
dbt test