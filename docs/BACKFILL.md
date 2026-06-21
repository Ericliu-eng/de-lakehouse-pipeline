# Backfill Runbook

## Purpose

Backfill processes an inclusive historical date range and records completed
dates in a local checkpoint so interrupted runs can resume.

## Command

```bash
make backfill START=2026-04-16 END=2026-04-18 SYMBOL=AAPL
```

`SYMBOL` defaults to `AAPL`. The equivalent CLI command is:

```bash
python -m de_lakehouse_pipeline.cli backfill --start 2026-04-16 --end 2026-04-18 --symbol AAPL
```

PostgreSQL must be running and migrated, and live execution requires
`ALPHA_VANTAGE_API_KEY`.

## Execution Flow

For each date in the requested range, the backfill:

1. Combines locally checkpointed dates with dates already present in PostgreSQL
   for the selected symbol.
2. Skips dates already marked as completed.
3. Fetches the Alpha Vantage daily payload and selects the target date.
4. Upserts matching rows into `market_bars` without the routine watermark
   filter.
5. Keeps the greater of the existing and backfilled timestamps as the
   watermark, preventing state from moving backward.
6. Marks the date complete only when PostgreSQL contains a row for that symbol
   and date.

## Checkpoint and Resume

Progress is stored in `.checkpoints/backfill_checkpoint.json`:

```json
{
  "completed_dates": [
    "2026-04-16",
    "2026-04-17"
  ]
}
```

If processing raises an exception, the failed date is not checkpointed. A
later run skips completed dates and retries the first incomplete date.

Deleting a date from the file alone does not force a rerun when that date still
exists in PostgreSQL, because checkpoint state is reconciled from the database
at startup. There is currently no explicit `--force` option.

## Validation

Run automated backfill tests:

```bash
make unit
```

Run a live one-day backfill:

```bash
make db-up
make db-migrate
make backfill START=2026-04-16 END=2026-04-16 SYMBOL=AAPL
```

Inspect the checkpoint with `Get-Content` in PowerShell or `cat` in Bash.

## Known Limitations

- The checkpoint stores completed dates globally rather than per symbol.
- Each target date triggers a separate Alpha Vantage request.
- Historical availability is limited to dates returned by the API payload.
- Weekend or unavailable dates are not marked complete because no database row
  is created.
- Completed dates cannot currently be rerun with a `--force` option.
