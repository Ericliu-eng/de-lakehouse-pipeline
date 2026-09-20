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
- `check_freshness(conn, table_name, timestamp_column, max_age_days, source=None, symbol=None)`
- `run_stock_quality_checks(conn, symbol, source="alpha_vantage")`

## Market-Bar Quality Gate

For `market_bars`, the gate verifies:

- `symbol` is not null
- `ts` is not null
- `(symbol, ts)` is unique
- `close` is non-negative
- `volume` is non-negative
- the latest `ts` for the active `(source, symbol)` is no more than 14 days old

### Scoped Freshness

The production stock quality gate filters freshness by `source` and `symbol`.
This prevents a recent row for one symbol from masking stale data for another
symbol. Filter values are passed as SQL parameters.

## Staging Schema Validation

Alpha Vantage records are mapped to the canonical market-bar schema before
type conversion. `validate_stock_row_schema()` verifies that every required
field is present and non-null.

Malformed records fail during staging, before PostgreSQL connectivity or
database writes.

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
