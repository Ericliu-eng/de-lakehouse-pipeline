# Data Quality Gates v1

## Current implementation

- `check_not_null(conn, table_name, column_name)`
- `check_unique(conn, table_name, column_name)`
- `check_range(conn, table_name, column_name, min_value=None, max_value=None)`
- `check_freshness(conn, table_name, timestamp_column, max_age_days)`
- `run_stock_quality_checks(conn)`

## Stock quality rules

For the `stock_prices` table, the quality gate validates:

- `symbol` is not NULL
- `ts` is not NULL
- `(symbol, ts)` is unique
- `close_price >= 0`
- `volume >= 0`
- latest `ts` is no more than 14 days old

## Validation

```bash
.venv/Scripts/python.exe -m pytest tests/unit/test_quality_checks.py -v
make test