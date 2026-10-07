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
proof logs. It exits with code 1 after any failed step, and code 0 after success.
It records top-level runs in `pipeline_runs` and sends best-effort PipeGuard
reports when configured. Row counts represent rows received from the source,
not the number newly loaded. Step details and quality results are emitted and
included in reports but are not written to the local child telemetry tables.

Manual `make run-marts` checks warehouse integrity in the same transaction as
the mart builds. Historical publication has no freshness requirement; daily
orchestration requires 0–14 day freshness for the active source and symbol.

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
- The Dagster job does not use the CLI runner's local run recording or PipeGuard
  reporting. Its step row count is not wired to the load result.
- Local step and quality-result persistence is not implemented.
- Concurrent ingestion and publication are not coordinated.
- Production alerting and orchestration-level retry policies are not configured.
