# Data Quality Gates v1

## Current implementation
- `check_not_null(conn, table_name, column_name)`
- `check_unique(conn, table_name, column_name)`

## Validation
```bash
.venv/Scripts/python.exe -m pytest tests/unit/test_quality_checks.py -v