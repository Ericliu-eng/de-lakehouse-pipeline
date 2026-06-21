# Architecture

## Overview

`de-lakehouse-pipeline` is a production-style market-data pipeline that
preserves raw Alpha Vantage payloads, incrementally loads normalized facts,
applies data-quality gates, builds analytical marts, and serves curated data.

## End-to-End Flow

```text
Alpha Vantage API
  -> Raw JSON Landing
  -> Typed Staging
  -> Watermark Read and Incremental Filter
  -> PostgreSQL Warehouse
  -> Data Quality Gate
  -> Analytical Marts
  -> FastAPI / Dashboard
```

The orchestrated path stops after a failed step, so marts are not rebuilt after
a quality failure.

## Component Catalog

| Component | Responsibility | Main implementation |
| --- | --- | --- |
| Ingestion | Fetch source data and preserve raw JSON | `src/de_lakehouse_pipeline/ingest/` |
| Staging | Convert source JSON into typed market-bar rows | `transform/staging/staging_market_bars.py` |
| Incremental processing | Read watermarks and select newer rows | `transform/incremental.py` |
| Warehouse loading | Upsert facts and operational metadata | `load/db/` |
| Data quality | Validate nulls, uniqueness, ranges, and freshness | `quality/checks.py` |
| Analytical marts | Build query-ready summary and snapshot tables | `transform/marts/`, `sql/marts/` |
| Orchestration | Run ingestion, quality, and marts in dependency order | `orchestration/` |
| Serving | Expose curated outputs through FastAPI and HTML | `src/serve/` |

## Storage Layers

| Layer | Purpose | Example |
| --- | --- | --- |
| Raw | Preserve source evidence for replay and debugging | `data/raw/.../stock.json` |
| Staging | Normalize payloads into typed in-memory rows | `StagedMarketBar` |
| Warehouse | Store facts and incremental state | `market_bars`, `pipeline_metadata` |
| Marts | Store curated analytical outputs | `mart_symbol_latest_price` |
| Serving | Provide consumer-facing access | `/latest-price`, `/dashboard` |

The warehouse schema is managed through versioned migrations, including
`migrations/003_market_bars.sql` and metadata/mart migrations.

## Data Model and Processing

`market_bars` is keyed by `(ts, symbol)`. Routine loads combine primary-key
upserts with a watermark per `(source, symbol)` to support idempotent reruns.
Backfills bypass routine filtering but prevent the watermark from moving
backward.

The current marts are:

- `mart_daily_symbol_summary`
- `mart_symbol_latest_price`
- `mart_symbol_volume_rank`

See `docs/DATA_MODEL.md` and `docs/INCREMENTAL.md` for details.

## Quality and Orchestration

The stock quality gate checks required keys, business-key uniqueness,
non-negative close and volume values, and freshness. A reusable foreign-key
check exists but is not part of the current stock gate.

Two local orchestration modes are available:

- `orchestration/dagster_pipeline.py`: deterministic CLI runner with JSON
  metrics.
- `orchestration/definitions.py`: Dagster job, local UI, and schedule
  definition.

See `docs/DATA_QUALITY.md` and `docs/ORCHESTRATION.md`.

## Serving Boundary

FastAPI reads from curated marts rather than raw payloads or staging objects.
This keeps consumer queries separate from ingestion internals and provides a
stable serving contract.

## Cloud Boundary

The repository includes an S3 raw-object layout, upload adapter, and Terraform
scaffold for an S3 bucket and least-privilege IAM policy. Runtime S3 client
creation and IAM role attachment are not yet integrated into the main pipeline.
See `docs/CLOUD_STORAGE.md`.

## Design Decisions

- Preserve raw source data before transformation.
- Separate raw, warehouse, mart, and serving concerns.
- Use primary keys, upserts, and watermarks for idempotency.
- Block mart publication when orchestrated quality checks fail.
- Serve curated tables instead of source-specific payloads.
- Keep local execution reproducible through Make targets.

Operational commands and troubleshooting live in `docs/RUNBOOK.md`; validation
evidence belongs under `docs/proof/`.
