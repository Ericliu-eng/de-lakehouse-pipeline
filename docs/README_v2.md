# de-lakehouse-pipeline (README v2)

A minimal production-style data engineering pipeline demonstrating:

* API ingestion
* raw JSON landing
* incremental database load with idempotent upsert
* backfill with checkpoint resume
* SQL-based marts
* reproducible workflows and CI-tested execution

This project is designed as a practical foundation for growing from
Data Engineering into MLOps, ML Systems, and AI Platform workflows.

---

## Overview

This pipeline ingests daily stock market data from Alpha Vantage, stores the
raw payload locally, loads new records into Postgres, and builds downstream
analytical marts from the raw table.

Current end-to-end flow:

```text
Alpha Vantage API
-> Raw Landing (JSON)
-> Parse / Type Conversion
-> Filter to target date
-> Incremental check via pipeline_metadata watermark
-> Upsert into Postgres market_bars
-> Record load metadata
-> Build marts
```

Key engineering goals:

* Reproducibility
* Modularity
* Safe reruns through idempotent load semantics
* Incremental ingestion using watermark tracking
* Testable, database-backed data workflows

---

## Architecture

```mermaid
graph TD
    A[Alpha Vantage API] --> B[Raw Landing: data/raw/YYYY-MM-DD/stock.json]
    B --> C[Parse Daily Time Series Payload]
    C --> D[Filter Rows For target_date]
    D --> E[Incremental Check via pipeline_metadata]
    E --> F[Upsert into market_bars]
    F --> G[Write load_metadata]
    F --> H[Update pipeline_metadata]
    F --> I[Marts Layer]

    subgraph "Analytical Marts"
        I1[mart_daily_symbol_summary]
        I2[mart_symbol_latest_price]
        I3[mart_symbol_volume_rank]
    end

    I --> I1
    I --> I2
    I --> I3
```

---

## Demo

```bash
git clone https://github.com/Ericliu-eng/de-lakehouse-pipeline.git
cd de-lakehouse-pipeline

cp .env.example .env

make setup
make db-up
make db-migrate
make run
make run-marts
make test
```

To run a historical backfill:

```bash
python -m de_lakehouse_pipeline.cli backfill --start 2026-04-16 --end 2026-04-18
```

To inspect the database:

```bash
make db-shell
```

Example verification queries:

```sql
SELECT COUNT(*) FROM market_bars;
SELECT * FROM market_bars ORDER BY ts DESC LIMIT 5;
SELECT * FROM pipeline_metadata;
SELECT * FROM load_metadata ORDER BY recorded_at DESC LIMIT 5;
```

---

## Pipeline Stages

### 1. Ingest

* Fetch daily stock data from the Alpha Vantage API
* Retry transient API failures
* Persist the raw response as a dated JSON artifact

Example output:

```text
data/raw/2026-05-27/stock.json
```

---

### 2. Parse and Normalize

* Read the landed JSON artifact
* Parse the nested daily time-series payload
* Convert fields into typed rows:
  `ts, symbol, open, high, low, close, volume`

---

### 3. Incremental Load

* Filter transformed rows to the requested `target_date`
* Read the last processed watermark from `pipeline_metadata`
* Keep only rows newer than the stored watermark
* Upsert rows into `market_bars`

Why this matters:

* reruns are safe
* duplicate loads are avoided
* the pipeline can resume incrementally

---

### 4. Metadata Tracking

Each successful run writes operational metadata:

* `pipeline_metadata`
  stores source, symbol, last watermark, row count, and status
* `load_metadata`
  stores load date, version, and record count for the run

This gives the pipeline a simple but useful observability layer.

---

### 5. Marts Layer

After raw data is loaded, analytical SQL marts can be rebuilt:

* `mart_daily_symbol_summary`
* `mart_symbol_latest_price`
* `mart_symbol_volume_rank`

These marts provide downstream-ready analytical outputs from the raw
`market_bars` table.

---

## Backfill Support

The pipeline supports date-range backfill through the unified CLI entrypoint:

```bash
python -m de_lakehouse_pipeline.cli backfill --start YYYY-MM-DD --end YYYY-MM-DD
```

Backfill behavior:

* iterates day by day through the requested range
* reuses the same stock pipeline logic as daily ingestion
* saves progress to `.checkpoints/backfill_checkpoint.json`
* skips dates already marked completed

This makes historical loading resumable after interruption.

---

## Database Schema

Core raw table:

```text
market_bars
-----------
ts timestamptz
symbol text
open numeric
high numeric
low numeric
close numeric
volume bigint
PRIMARY KEY (ts, symbol)
```

Operational tables:

* `pipeline_metadata`
* `load_metadata`

This design supports:

* time-series storage
* deduplication via composite key
* incremental ingestion
* operational tracking for loads

---

## Reproducible Workflows

Common commands:

```bash
make setup        # create venv and install deps
make lint         # run ruff
make db-up        # start Postgres container
make db-down      # stop Postgres container
make db-migrate   # apply database schema
make run          # run the daily stock pipeline
make run-marts    # build analytical marts
make test         # run test suite
make smoke        # run smoke tests
make db-shell     # open psql shell in container
```

---

## Testing Strategy

### Unit Tests

* transformation parsing logic
* incremental filtering behavior
* SQL utility and quality logic
* database configuration helpers

### Smoke Tests

* end-to-end pipeline execution
* database connectivity
* migration and load verification

This layered test strategy helps protect both code behavior and data workflow reliability.

---

## SQL Layer

The project includes reusable SQL assets for both validation and analytics:

* `sql/quality_checks.sql`
* `sql/patterns_window.sql`
* `sql/marts/*.sql`

These SQL files support data quality checks, analytical transformations,
and reusable warehouse patterns.

---

## CI

On pull requests, CI is intended to validate reproducibility through steps such as:

* environment setup
* lint checks
* database migration
* smoke tests
* full pytest suite

This keeps the local workflow aligned with automated verification.

---

## Why This Project

This project demonstrates practical engineering concepts:

* external API ingestion
* raw data landing
* incremental and idempotent load design
* operational metadata tracking
* SQL-based mart construction
* reproducible local and CI workflows

It is a compact project, but it already reflects patterns that scale toward:

* feature pipelines
* MLOps systems
* AI platform data foundations

---
