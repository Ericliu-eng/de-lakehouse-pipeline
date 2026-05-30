# Orchestration

## Purpose

The local orchestration layer provides a reproducible command that executes the
main stock pipeline, validates data quality, and rebuilds marts in a fixed
order.

The implementation lives in:

```text
orchestration/dagster_pipeline.py
```

Despite the filename, this is currently a lightweight local orchestrator rather
than a Dagster runtime deployment.

## Execution Order

`make -f Makefile orchestrate SYMBOL=AAPL` runs:

1. `run_stock_pipeline`
   - fetches Alpha Vantage data
   - lands raw JSON
   - stages typed market-bar rows
   - performs incremental filtering
   - upserts new rows into `market_bars`
   - updates load and pipeline metadata
2. `run_quality_checks`
   - runs the stock quality gate against `market_bars`
   - fails the orchestration run if any check fails
3. `build_marts`
   - rebuilds analytical marts in dependency order
   - `mart_daily_symbol_summary`
   - `mart_symbol_latest_price`
   - `mart_symbol_volume_rank`

If a step fails, later steps are not executed and the pipeline status is
reported as `failed`.

## Command

```bash
make -f Makefile orchestrate SYMBOL=AAPL
```

Or directly:

```bash
python -m orchestration.dagster_pipeline --symbol AAPL
```

## Metrics

Each step records:

- step name
- status
- start timestamp
- finish timestamp
- duration in seconds
- row count when available
- error message when failed

The final pipeline summary records the overall status and all executed step
metrics. The command also prints a JSON metrics payload so the run can be
copied into proof logs or parsed by a later monitoring layer.

## Structured Logs

The orchestrator configures JSON logs through:

```text
src/de_lakehouse_pipeline/logging_utils.py
```

Logs include the pipeline name, symbol, step name, status, row counts when
available, and exception details on failure.

## Requirements

- Postgres must be running and migrated.
- The live stock step requires `ALPHA_VANTAGE_API_KEY`.
- For API-independent validation, use `make -f Makefile smoke-db`.

## Known Limitations

- This is local orchestration, not a scheduled Dagster deployment.
- The stock pipeline currently returns a raw file path, so the orchestrator does
  not yet report a loaded-row count for that step.
- Failure metadata is reported in the run summary but is not yet persisted to a
  database table.
