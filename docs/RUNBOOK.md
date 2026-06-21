# Local Operations Runbook

## Purpose

Use this runbook to start, validate, operate, inspect, and troubleshoot the
local market-data pipeline.

## Prerequisites

- Python for creating the virtual environment.
- Docker and Docker Compose for PostgreSQL.
- `.env` with the required database settings.
- `ALPHA_VANTAGE_API_KEY` for live ingestion.

## Five-Minute Demo

Prepare the project and database:

```bash
make setup
make db-up
make db-migrate
```

Validate and run the pipeline:

```bash
make lint
make test
make run SYMBOL=AAPL
make run-marts
```

Start the serving layer:

```bash
python -m src.serve.api
```

Open:

- <http://127.0.0.1:8000/health>
- <http://127.0.0.1:8000/latest-price>
- <http://127.0.0.1:8000/dashboard>

`make test` includes database-backed integration tests, so PostgreSQL must be
running and migrated first.

## Validation Commands

| Command | Scope | PostgreSQL required |
| --- | --- | --- |
| `make lint` | Static analysis | No |
| `make unit` | Unit tests | No |
| `make smoke` | Lightweight smoke tests | No |
| `make integration` | Marts and metadata integration tests | Yes |
| `make smoke-db` | Database smoke tests | Yes |
| `make test` | Unit, smoke, and integration tests | Yes |
| `make test-all` | Complete test suite | Yes |

## Common Operations

Run ingestion and build marts:

```bash
make run SYMBOL=AAPL
make run-marts
```

Run the quality-gated local orchestrator or open Dagster:

```bash
make orchestrate SYMBOL=AAPL
make dagster-dev
```

Run a historical backfill:

```bash
make backfill START=2026-04-16 END=2026-04-18 SYMBOL=AAPL
```

See `docs/ORCHESTRATION.md`, `docs/INCREMENTAL.md`, and `docs/BACKFILL.md` for
behavior and limitations.

## Database Inspection

Open a PostgreSQL shell:

```bash
make db-shell
```

Inspect warehouse, state, load history, and serving data:

```sql
SELECT COUNT(*) AS market_bar_count FROM market_bars;

SELECT * FROM pipeline_metadata ORDER BY updated_at DESC;

SELECT * FROM load_metadata ORDER BY recorded_at DESC LIMIT 10;

SELECT *
FROM mart_symbol_latest_price
ORDER BY latest_ts DESC
LIMIT 10;
```

## Troubleshooting

| Symptom | Check or recovery |
| --- | --- |
| PostgreSQL unavailable | Run `make db-up`, check `docker ps`, then run `make db-migrate` |
| No new rows | Inspect `pipeline_metadata`; an unchanged watermark is expected on an idempotent rerun |
| Data-quality failure | Check null `symbol`/`ts` values and duplicate `(symbol, ts)` keys; see `docs/DATA_QUALITY.md` |
| API or write failure | Inspect structured logs and `docs/FAILURE_DRILLS.md` before rerunning |
| Serving layer has no data | Run ingestion and marts, then inspect `mart_symbol_latest_price` |

Not every upstream HTTP failure is currently retried. Consult the failure
drills for verified safeguards and known gaps.

## Shutdown

```bash
make db-down
```
