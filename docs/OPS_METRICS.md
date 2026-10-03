# Operational Metrics

## Overview

The project provides lightweight observability for local pipeline runs through
execution metrics, structured JSON logs, and SLA evaluation helpers.

Implementation:

```text
src/de_lakehouse_pipeline/metrics.py
src/de_lakehouse_pipeline/logging_utils.py
src/de_lakehouse_pipeline/observability/run_repository.py
```

## Captured Metrics

Each local orchestration run records:

- pipeline and step names
- UTC start and finish timestamps
- success or failure status
- duration in seconds
- row count when available
- error details on failure

The orchestrator stops after a failed step and emits the final run summary as
JSON. Structured logs also include operational context such as `symbol`,
`step_name`, `status`, and `row_count`.

The lightweight orchestrator also creates a durable `pipeline_runs` row before
executing the first step. It finalizes that row as `SUCCESS` or `FAILED`, with
elapsed time, quality status, and the first failed step's exception type and
message. The initial insert is committed separately so a later pipeline
failure cannot erase the evidence that the run started.

`rows_processed` is the number of rows the source returned and staging
accepted, not the number newly loaded. The load is incremental, so new rows
are about one per trading day and zero on weekends and holidays; a drop in
that number is normal. The number received stays near the size of the
requested window, and a drop in it means the source sent less than usual.

## Reporting to PipeGuard

When `PIPEGUARD_API_URL` and `PIPEGUARD_API_KEY` are set, each finished run is
reported to [PipeGuard](https://github.com/Ericliu-eng/pipeguard) with its status, timing, row count, error, and
the result of every quality check, including the checks of a run that stopped
on bad data. The run's `external_run_id` UUID doubles as the report's
idempotency key, so a resent report is recognised instead of counted twice.

PipeGuard adds the one check a run cannot make about itself: whether its row
count collapsed compared with earlier runs. The in-batch checks here ask whether
*this* data is valid; a truncated response can pass every one of them.

Reporting never affects the run. The local `pipeline_runs` row is written
first, the report uses a 5-second timeout (`PIPEGUARD_TIMEOUT_SECONDS`), and
any failure — unreachable, rejected, or a defect in the reporter itself — is
logged and the run continues. With either variable unset, nothing is sent.

Implementation: `src/de_lakehouse_pipeline/observability/pipeguard_reporter.py`.

## SLA Evaluation

| Signal | Definition | Default target |
| --- | --- | --- |
| Data freshness | Age of the latest source record | 1,440 minutes |
| Pipeline latency | Time from pipeline start to finish | 300 seconds |
| Failure rate | Failed runs divided by total runs | 5% |

Missing freshness or latency values fail evaluation. These thresholds are local
engineering targets, not measured production SLA claims.

Failures can also be classified as `retryable`, `non_retryable`, or `unknown`
for future retry and alerting policies.

## Run and Validate

```bash
make orchestrate SYMBOL=AAPL
make unit
make smoke
```

Database-backed validation, including successful and failed run persistence,
requires PostgreSQL:

```bash
make db-up
make db-migrate
make smoke-db
```

## Current Limitations

- Pipeline-level run status, timing, rows received, and errors are persisted;
  step-level rows are not. Individual quality-check results are reported to
  PipeGuard but not stored locally.
- SLA evaluation is not automatically attached to every pipeline run.
- Failure classification does not yet trigger retry policies.
- Runs are monitored externally by PipeGuard, but alerting is not configured.
- Only CLI-orchestrated runs are recorded and reported; the Dagster scheduled
  job runs its own ops and bypasses both.
- The marts step does not return a row count.
