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
make db-seed
```

Validate and run the pipeline:

```bash
make lint
make unit
make smoke
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

Run the complete database suite separately against a disposable database using
`make test-all`; tests delete rows. CI provisions and migrates its own database.

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

`run-marts` checks warehouse integrity before building any mart and preserves
the previous marts on failure. It accepts valid historical data. The daily
orchestrator additionally requires 0–14 day freshness for its active partition.
Run ingestion and publication serially.

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

Replay the benchmark without external source or monitoring requests:

```bash
python -m scripts.benchmark --repeats 3 --scale-repeats 3
```

The configured PostgreSQL user needs CREATE DATABASE permission. The script
creates a unique database, refuses existing names, and drops only the database
it successfully created. `--keep-db` retains it for inspection. S3 and
PipeGuard are disabled, and temporary raw files/checkpoints are isolated.

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
| Data-quality failure | Inspect keys, finite non-negative OHLCV, price ranges, future trading dates, and scoped freshness; see `docs/DATA_QUALITY.md` |
| API or write failure | Inspect structured logs and `docs/FAILURE_DRILLS.md` before rerunning |
| Serving layer has no data | Run ingestion and marts, then inspect `mart_symbol_latest_price` |

Not every upstream HTTP failure is currently retried. Consult the failure
drills for verified safeguards and known gaps.

### Recovering an existing future watermark

New loads reject future dates before writes. To repair data created by older
code, stop ingestion/publication, back up the database, and inspect future rows:

```sql
SELECT source, symbol, ts FROM market_bars
WHERE (ts AT TIME ZONE 'America/New_York')::date
    > (CURRENT_TIMESTAMP AT TIME ZONE 'America/New_York')::date;
```

After confirming those rows are invalid, remove them for the affected partition
and reset its watermark from the remaining valid facts. For example, for
`alpha_vantage/AAPL`:

```sql
BEGIN;
DELETE FROM market_bars
WHERE source = 'alpha_vantage' AND symbol = 'AAPL'
  AND (ts AT TIME ZONE 'America/New_York')::date
    > (CURRENT_TIMESTAMP AT TIME ZONE 'America/New_York')::date;
UPDATE pipeline_metadata SET last_watermark = (
    SELECT MAX(ts) FROM market_bars
    WHERE source = 'alpha_vantage' AND symbol = 'AAPL'
), updated_at = CURRENT_TIMESTAMP
WHERE source = 'alpha_vantage' AND symbol = 'AAPL';
DELETE FROM mart_symbol_volume_rank WHERE symbol = 'AAPL';
DELETE FROM mart_daily_symbol_summary WHERE symbol = 'AAPL';
DELETE FROM mart_symbol_latest_price WHERE symbol = 'AAPL';
COMMIT;
```

Run `make run-marts` to recreate that symbol's outputs from valid facts, then
`make orchestrate SYMBOL=AAPL` to resume incremental loading. Preserve load
audit history as evidence. The explicit mart cleanup is necessary because
normal upsert builds do not propagate source deletions.

## Shutdown

```bash
make db-down
```
