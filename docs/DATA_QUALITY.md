# Data Quality Gates v1

## Current implementation

- `check_not_null(conn, table_name, column_name)`
- `check_unique(conn, table_name, column_name)`
- `check_range(conn, table_name, column_name, min_value=None, max_value=None)`
- `check_foreign_key(conn, child_table, child_column, parent_table, parent_column)`
- `check_freshness(conn, table_name, timestamp_column, max_age_days)`
- `run_stock_quality_checks(conn)`

## Stock quality rules

For the `market_bars` table, the quality gate validates:

- `symbol` is not NULL
- `ts` is not NULL
- `(symbol, ts)` is unique
- `close >= 0`
- `volume >= 0`
- latest `ts` is no more than 14 days old

The project also includes a reusable foreign-key quality check. It is not part
of `run_stock_quality_checks` yet because the current `market_bars` model does
not have a parent dimension table.

## Validation

```bash
.venv/Scripts/python.exe -m pytest tests/unit/test_quality_checks.py -v
make test
