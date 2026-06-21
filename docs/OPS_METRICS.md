# Operational Metrics

## Overview

The project provides lightweight observability for local pipeline runs through
execution metrics, structured JSON logs, and SLA evaluation helpers.

Implementation:

```text
src/de_lakehouse_pipeline/metrics.py
src/de_lakehouse_pipeline/logging_utils.py
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

Database-backed validation requires PostgreSQL:

```bash
make db-up
make db-migrate
make smoke-db
```

## Current Limitations

- Metrics are emitted as logs and JSON but are not persisted.
- SLA evaluation is not automatically attached to every pipeline run.
- Failure classification does not yet trigger retry policies.
- External monitoring, dashboards, and alerting are not configured.
- Some steps do not return an accurate processed-row count.
