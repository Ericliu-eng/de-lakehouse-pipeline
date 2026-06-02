# Backfill Runbook
## Purpose
Backfill loads historical stock data across a date range while preserving
resume behavior through a local checkpoint file.

## Command

Run through the project CLI:
```bash
python -m de_lakehouse_pipeline.cli backfill --start 2026-04-16 --end 2026-04-18 --symbol AAPL
```
Or through Makefile:
```bash
make -f Makefile backfill START=2026-04-16 END=2026-04-18 SYMBOL=AAPL
```
`SYMBOL` defaults to `AAPL` when omitted.

## Checkpoint Path

Backfill progress is stored in:

```text
.checkpoints/backfill_checkpoint.json
```

The checkpoint stores completed dates:

```json
{
  "completed_dates": [
    "2026-04-16",
    "2026-04-17"
  ]
}
```

## Resume Behavior

When a backfill starts, it reads the checkpoint and skips dates that are already
marked completed.

A date is marked completed only after that date's pipeline run finishes
successfully.

## Failure Behavior

If a date fails, the exception is raised and that date is not added to the
checkpoint.

On the next run, earlier completed dates are skipped and the failed date is
retried.

## Rerunning a Date

To force a date to rerun, remove that date from
`.checkpoints/backfill_checkpoint.json`, then run the same backfill command
again.

Because the load path uses watermark filtering and upserts into `market_bars`,
normal reruns remain safe.

## Validation

Run unit tests:

```bash
make -f Makefile unit
```

Run a one-day backfill:

```bash
make -f Makefile backfill START=2026-04-16 END=2026-04-16 SYMBOL=AAPL
```

Inspect checkpoint state:

```bash
type .checkpoints\backfill_checkpoint.json
```

## Known Limitations

- The checkpoint currently tracks completed dates only, not per-symbol
  completion state.
- The live backfill path requires an Alpha Vantage API key.
- Historical corrections older than the pipeline watermark may be skipped by
  the incremental load strategy.
