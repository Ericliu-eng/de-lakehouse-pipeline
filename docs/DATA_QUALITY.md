# Data Quality Gates

## Overview

The pipeline applies reusable SQL quality checks before rebuilding analytical
marts. Any failed stock quality check stops orchestration, preventing invalid
warehouse data from being published downstream.

## Available Checks

- `check_not_null(conn, table_name, column_name)`
- `check_unique(conn, table_name, column_name)`
- `check_range(conn, table_name, column_name, min_value=None, max_value=None)`
- `check_foreign_key(conn, child_table, child_column, parent_table, parent_column)`
- `check_freshness(conn, table_name, timestamp_column, max_age_days)`
- `run_stock_quality_checks(conn)`

## Market-Bar Quality Gate

For `market_bars`, the gate verifies:

- `symbol` is not null
- `ts` is not null
- `(symbol, ts)` is unique
- `close` is non-negative
- `volume` is non-negative
- the latest `ts` is no more than 14 days old

### Freshness Scope Limitation

The current query uses `MAX(ts)` across the entire `market_bars` table. It does
not filter by `source` or `symbol`, so a fresh partition can mask a stale one.
Per-partition freshness is a release blocker; see `docs/PROJECT_STATUS.md`.

The required-field validator in `quality/schema_validation.py` is also not yet
invoked by the production staging path. Source conversion currently raises on
many malformed values, but the dedicated contract check remains test-only.

The reusable foreign-key check is not part of this gate because the current
market-bar model has no parent dimension table.

## Validation

Run unit checks:

```bash
make unit
```

Run database-backed quality validation:

```bash
make db-up
make db-migrate
make smoke-db
```

For end-to-end execution through the quality gate, run:

```bash
make orchestrate SYMBOL=AAPL
```
