# Orchestration

## Overview

The project provides two local orchestration modes:

1. A lightweight CLI runner for repeatable execution and JSON metrics.
2. A Dagster job for dependency-aware execution, scheduling, and UI visibility.

Both modes run the same quality-gated workflow:

```text
Stock Ingestion -> Data Quality Gate -> Analytical Marts
```

## Execution Flow

1. `run_stock_pipeline`
   - fetches and preserves the raw payload
   - transforms and incrementally loads market bars
   - updates pipeline and load metadata
2. `run_quality_checks`
   - validates warehouse data
   - stops the workflow when any check fails
3. `build_marts`
   - builds daily summary, latest price, and volume-rank marts

Later steps are skipped after a failure, preventing invalid data from being
published to analytical marts.

## Lightweight Runner

Implementation: `orchestration/dagster_pipeline.py`

```bash
make orchestrate SYMBOL=AAPL
```

The runner prints step results and a JSON pipeline summary for validation and
proof logs.

## Dagster Job

Implementation: `orchestration/definitions.py`

```bash
make dagster-dev
```

Dagster provides explicit step dependencies, UI logs, the
`stock_lakehouse_job` definition, and a daily `0 8 * * *` schedule definition.
The schedule is defined locally but is not deployed.

## Requirements

- Project dependencies are installed with `make setup`.
- PostgreSQL is running and migrated.
- `ALPHA_VANTAGE_API_KEY` is available for live ingestion.

See `docs/RUNBOOK.md` for setup and validation commands. See
`docs/OPS_METRICS.md` for metrics, logging, and SLA evaluation.

## Current Limitations

- Dagster is configured for local development rather than production hosting.
- Metrics are emitted but not persisted to an observability store.
- The ingestion step does not report an accurate loaded-row count.
- The lightweight runner reports failure but does not return a non-zero process
  exit code.
- Production alerting and orchestration-level retry policies are not configured.
