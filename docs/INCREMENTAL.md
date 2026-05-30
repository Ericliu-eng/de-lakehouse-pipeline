# Incremental Loading

## Purpose

The stock pipeline uses incremental loading so repeated runs are safe and do
not duplicate already processed market bars.

## Watermark Table

Incremental state is stored in `pipeline_metadata`.

The table is keyed by `(source, symbol)` and records:

- `last_watermark`: latest processed market timestamp
- `last_row_count`: number of rows written in the last successful load
- `status`: latest load status
- `updated_at`: metadata update timestamp

## Algorithm

For each stock pipeline run:

1. Fetch and land the raw Alpha Vantage payload.
2. Stage raw records into typed market-bar rows.
3. Read the latest watermark for `(source, symbol)`.
4. Keep only rows whose timestamp is greater than the watermark.
5. Upsert the new rows into `market_bars`.
6. Update the watermark to the max timestamp from the new rows.
7. Record load metadata.

## Idempotency Guarantees

The pipeline is safe to rerun because:

- watermark filtering skips rows older than or equal to the last processed
  timestamp
- `market_bars` uses `(ts, symbol)` as its primary key
- writes use upsert semantics instead of append-only inserts

Together, these rules prevent duplicate market-bar rows during normal reruns.

## Rerun Behavior

On the first run for a symbol, the watermark is missing, so all staged rows are
eligible for loading.

On a later run with the same data, every row is older than or equal to the
stored watermark, so no rows are loaded and the existing row count stays stable.

## Known Limitations

- The current watermark strategy is timestamp-based, so very late-arriving
  corrections with timestamps older than the watermark are skipped.
- The current implementation tracks one watermark per `(source, symbol)`.
- The loader does not yet record failed watermark updates as failed pipeline
  metadata events.

## Validation

Run unit tests:

```bash
make -f Makefile unit
```

Run DB-backed smoke validation:

```bash
make -f Makefile smoke-db
```
