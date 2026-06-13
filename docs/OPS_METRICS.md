# Operational Metrics

## Purpose

This project includes a lightweight observability layer for tracking pipeline
execution. The goal is to make each run easier to inspect, debug, and validate.

## Metrics Captured

The metrics layer records:

- pipeline name
- pipeline start time
- pipeline end time
- pipeline status
- pipeline duration in seconds
- step name
- step start time
- step end time
- step status
- step duration in seconds
- row count, when available
- error message, when a step fails

## Current Implementation

Metrics and structured logging are implemented in:

```text
src/de_lakehouse_pipeline/metrics.py
src/de_lakehouse_pipeline/logging_utils.py
```

The local orchestrator records a `PipelineMetric` for every run and a
`StepMetric` for each executed step.

Current orchestrated steps:

1. `run_stock_pipeline`
2. `run_quality_checks`
3. `build_marts`

If a step fails, the orchestrator stops immediately, marks the pipeline as
`failed`, and includes the failed step error message in the final summary.

## Structured Logging

CLI and orchestration entrypoints configure JSON logs with:

- UTC timestamp
- log level
- logger name
- message
- module
- structured fields such as `command`, `symbol`, `step_name`, `status`, and
  `row_count`

Example log shape:

```json
{
  "level": "INFO",
  "logger": "orchestration.dagster_pipeline",
  "message": "Finished orchestration step",
  "module": "dagster_pipeline",
  "row_count": 3,
  "status": "success",
  "step_name": "build_marts",
  "timestamp": "2026-05-30T10:00:00+00:00"
}
```

## How To Run

```bash
make -f Makefile orchestrate SYMBOL=AAPL
```

For API-independent validation:

```bash
make -f Makefile unit
make -f Makefile smoke-db
```

## SLA Reporting

The SLA report summarizes operational health for pipeline runs:

- data freshness: minutes between the latest available source data and check time
- pipeline latency: seconds between pipeline start and finish
- failure rate: failed runs divided by total runs

Default thresholds:

- freshness: 1440 minutes
- latency: 300 seconds
- failure rate: 0.05

Failure classification:

- retryable: timeout, rate_limit, connection, temporary, server_error
- non-retryable: schema, validation, auth, not_found, bad_request

Validation commands:

```bash
pytest tests/unit/test_metrics.py
pytest tests/smoke/test_metrics_sla_smoke.py
make lint
make test