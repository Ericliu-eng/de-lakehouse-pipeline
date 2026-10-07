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
- `check_market_bar_values(conn)`
- `run_market_bar_quality_checks(conn)`
- `run_stock_quality_checks(conn, symbol, source="alpha_vantage")`

## Market-Bar Quality Gate

For `market_bars`, the gate verifies:

- `symbol` is not null
- `ts` is not null
- `(symbol, ts)` is unique
- `close` is non-negative
- `volume` is non-negative
- all OHLC prices are present, finite, non-negative, and satisfy
  `low <= open/close <= high`; volume is present and non-negative, and no
  trading date is in the future
- the latest `ts` for the active `(source, symbol)` is between 0 and 14 days old

Daily CLI orchestration and Dagster run all seven checks. Manual
`make run-marts` runs the six warehouse integrity checks before building any
mart, in the same transaction as the builds. It permits historical datasets
without requiring a recent bar. A failed check preserves existing mart rows.

### Scoped Freshness

The production stock quality gate filters freshness by `source` and `symbol`.
This prevents a recent row for one symbol from masking stale data for another
symbol. Filter values are passed as SQL parameters.
Age is calculated using calendar dates in `America/New_York`, independent of
the database session time zone. Future timestamps fail the freshness check.

## Staging Schema Validation

Both Alpha Vantage and Tiingo records are mapped to the canonical market-bar
schema before type conversion. `validate_stock_row_schema()` checks required
fields, timezone-aware timestamps, future trading dates, finite non-negative
prices, OHLC consistency, and integral volume in PostgreSQL BIGINT range.
Fractional volume is rejected rather than truncated.

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

Regression tests cover invalid inputs for both sources before database access
(`tests/unit/test_market_bar_validation.py`) and existing invalid warehouse
rows blocking manual publication on real PostgreSQL
(`tests/integration/test_mart_quality_gate.py`). These safeguards assume serial
execution; concurrent ingestion and publication are not coordinated.
