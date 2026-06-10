# Architecture

## Purpose

`de-lakehouse-pipeline` is a production-style data engineering pipeline for
stock market data. It ingests raw Alpha Vantage payloads, stores raw data,
loads normalized rows into Postgres, builds analytical marts, validates data
quality, and exposes curated results through a small serving API and dashboard.

## High-Level Flow

```text
Alpha Vantage API
  -> Raw JSON landing
  -> Staging transform
  -> Postgres market_bars
  -> Incremental watermark
  -> Data quality checks
  -> Analytical marts
  -> Serving API / dashboard
```

## Main Components

### Ingestion

The ingestion layer fetches daily stock data from Alpha Vantage and saves the
raw response as JSON. The project also supports optional S3 upload for cloud
raw storage.

Key files:

- `src/de_lakehouse_pipeline/ingest/market_data_client.py`
- `src/de_lakehouse_pipeline/ingest/io.py`
- `src/de_lakehouse_pipeline/ingest/cloud_storage.py`

### Staging

The staging layer converts raw Alpha Vantage JSON into typed market bar rows
with a consistent column order for database loading.

Key files:

- `src/de_lakehouse_pipeline/transform/staging/staging_market_bars.py`

### Load

The load layer writes staged rows into Postgres. The main fact table is
`market_bars`, keyed by `(ts, symbol)`. Writes are idempotent so reruns do not
create duplicate records.

Key files:

- `src/de_lakehouse_pipeline/load/loader.py`
- `src/de_lakehouse_pipeline/load/db/stock_writer.py`
- `migrations/003_stock_prices.sql`

### Incremental Processing

The pipeline tracks the latest processed timestamp in `pipeline_metadata`. On
each run, it filters out rows that have already been processed for the same
source and symbol.

Key files:

- `src/de_lakehouse_pipeline/transform/incremental.py`
- `src/de_lakehouse_pipeline/load/db/pipeline_metadata.py`
- `docs/INCREMENTAL.md`

### Data Quality

The quality layer checks core data guarantees before downstream use. Current
checks include not-null, uniqueness, numeric range, foreign key helper logic,
and freshness.

Key files:

- `src/de_lakehouse_pipeline/quality/checks.py`
- `sql/quality_checks.sql`
- `docs/DATA_QUALITY.md`

### Analytical Marts

The marts layer creates curated tables for downstream querying and dashboard
use.

Current marts:

- `mart_daily_symbol_summary`
- `mart_symbol_latest_price`
- `mart_symbol_volume_rank`

Key files:

- `sql/marts/`
- `src/de_lakehouse_pipeline/transform/marts/`
- `docs/DATA_MODEL.md`
- `docs/DEMO_QUERIES.md`

### Serving

The serving layer exposes curated data through FastAPI and a minimal dashboard.
The `/latest-price` endpoint reads from Postgres and returns the latest
available price record.

Key files:

- `src/serve/api.py`
- `src/serve/templates/dashboard.html`

## Orchestration

The local orchestrator runs the pipeline in a fixed order:

1. Run stock ingestion and load.
2. Run data quality checks.
3. Build analytical marts.

Key files:

- `orchestration/dagster_pipeline.py`
- `docs/ORCHESTRATION.md`

## Storage Layers

| Layer | Purpose | Example |
| --- | --- | --- |
| Raw | Preserve original source payloads | `data/raw/.../stock.json` |
| Staging | Convert raw payloads into typed rows | Python staging functions |
| Warehouse | Store normalized facts and metadata | Postgres `market_bars`, `pipeline_metadata` |
| Marts | Store curated query-ready outputs | `mart_symbol_latest_price` |
| Serving | Expose selected outputs | FastAPI `/latest-price`, `/dashboard` |

## Validation Strategy

The project uses layered validation:

- Unit tests for individual functions.
- Smoke tests for lightweight end-to-end paths.
- DB-backed integration tests for marts and metadata behavior.
- Ruff linting for code quality.
- GitHub Actions CI for repeatable validation.

Common commands:

```bash
make lint
make unit
make smoke
make integration
make test
```

## Local Demo Path

A typical local run is:

```bash
make db-up
make db-migrate
make run
make run-marts
python -m src.serve.api
```

Then open:

```text
http://127.0.0.1:8000/health
http://127.0.0.1:8000/latest-price
http://127.0.0.1:8000/dashboard
```

## Design Principles

- Keep raw data separate from transformed data.
- Make database writes idempotent.
- Use watermarks for safe incremental processing.
- Run data quality checks before serving curated outputs.
- Keep local development reproducible through Makefile commands.
- Keep serving focused on marts and curated data, not raw source payloads.
