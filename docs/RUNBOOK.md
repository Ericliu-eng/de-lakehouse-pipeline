# Runbook

## Purpose

This runbook describes how to run, validate, inspect, and troubleshoot the
local `de-lakehouse-pipeline` workflow. It is intended for local demos,
development checks, and quick incident-style debugging.

## Prerequisites

- Python virtual environment is created with `make setup`.
- `.env` exists and contains the database settings.
- Docker is available for the local Postgres service.
- `ALPHA_VANTAGE_API_KEY` is set for live API ingestion.

For API-independent checks, use the unit, smoke, and integration tests.

## Common Local Workflow

Start Postgres and apply migrations:

```bash
make db-up
make db-migrate
```

Run the stock pipeline and build marts:

```bash
make run
make run-marts
```

Run the serving API:

```bash
python -m src.serve.api
```

Open:

```text
http://127.0.0.1:8000/health
http://127.0.0.1:8000/latest-price
http://127.0.0.1:8000/dashboard
```

## Validation Commands

Use these commands before opening a PR or recording proof:

```bash
make lint
make unit
make smoke
make integration
make test
```

Notes:

- `make unit` is the fastest code-level check.
- `make smoke` validates lightweight end-to-end behavior.
- `make integration` validates DB-backed marts and metadata behavior.
- `make test` runs unit, smoke, and integration tests.

## Database Inspection

Open a Postgres shell:

```bash
make db-shell
```

Useful queries:

```sql
SELECT COUNT(*) FROM market_bars;

SELECT *
FROM pipeline_metadata
ORDER BY updated_at DESC;

SELECT *
FROM mart_symbol_latest_price
ORDER BY latest_ts DESC
LIMIT 10;

SELECT *
FROM load_metadata
ORDER BY recorded_at DESC
LIMIT 10;
```

## Backfill Workflow

Run a date-range backfill:

```bash
python -m de_lakehouse_pipeline.cli backfill --start 2026-04-16 --end 2026-04-18 --symbol AAPL
```

See `docs/BACKFILL.md` for checkpoint and resume behavior.

## Orchestrated Workflow

Run the local orchestrator:

```bash
make orchestrate SYMBOL=AAPL
```

The orchestrator runs:

1. Stock ingestion and load.
2. Data quality checks.
3. Mart builds.

See `docs/ORCHESTRATION.md` for step metrics and known limitations.

## Troubleshooting

### Postgres Is Not Reachable

Symptoms:

- Connection refused.
- `wait_for_db` times out.
- DB-backed tests fail immediately.

Checks:

```bash
make db-up
docker ps
make db-migrate
```

If the schema is missing, rerun migrations:

```bash
make db-migrate
```

### No New Rows Are Loaded

Symptoms:

- Pipeline succeeds but row count does not increase.
- Logs say no new rows were found.

Likely cause:

- Incremental watermark already points to the latest loaded timestamp.

Checks:

```sql
SELECT *
FROM pipeline_metadata
WHERE source = 'alpha_vantage';
```

This is expected for idempotent reruns. To test new data, run with a different
symbol or use a fixture-backed test path.

### Quality Checks Fail

Symptoms:

- Orchestrator stops before building marts.
- `run_stock_quality_checks` reports failed checks.

Checks:

```sql
SELECT COUNT(*) FROM market_bars WHERE symbol IS NULL;
SELECT COUNT(*) FROM market_bars WHERE ts IS NULL;

SELECT symbol, ts, COUNT(*)
FROM market_bars
GROUP BY symbol, ts
HAVING COUNT(*) > 1;
```

See `docs/DATA_QUALITY.md` for the full quality gate.

### API Rate Limit Or Upstream Failure

Symptoms:

- Alpha Vantage request fails.
- Retryable API errors such as 429 or 500 are reported.

Expected behavior:

- Retry retryable failures.
- Fail clearly after max retries.
- Do not load corrupted rows.
- Do not advance the watermark on failed loads.

See `docs/FAILURE_DRILLS.md` for reliability drill expectations.

### Serving API Returns No Data

Symptoms:

- `/latest-price` fails or returns no record.
- Dashboard has no useful output.

Checks:

```bash
make db-up
make db-migrate
make run
make run-marts
python -m src.serve.api
```

Then inspect the mart:

```sql
SELECT *
FROM mart_symbol_latest_price
ORDER BY latest_ts DESC
LIMIT 5;
```

The serving layer should read curated mart data rather than raw source payloads.

## Proof Checklist

For weekly proof, save at least one of:

- Terminal output from validation commands.
- Browser screenshot of `/latest-price` or `/dashboard`.
- Orchestrator summary output.
- DB query output showing loaded rows or mart records.

Store proof under:

```text
docs/proof/
```

## Shutdown

Stop the local database when finished:

```bash
make db-down
```

## Metrics and SLA

This pipeline tracks three production-style reliability metrics:

1. Data Freshness
   - Measures how old the latest available data is.
   - Example SLA: latest market data should be available within 24 hours.

2. Pipeline Latency
   - Measures how long the pipeline takes from ingestion to transformed output.
   - Example SLA: daily run should finish within 5 minutes.

3. Failure Rate
   - Measures failed pipeline runs divided by total runs.
   - Example SLA: failure rate should stay below 5%.
