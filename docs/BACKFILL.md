# Backfill Strategy

## Goal

Support safe reruns and prepare the pipeline for historical backfills.

The current Week 09 implementation focuses on idempotent incremental
processing. A pipeline run should only load records newer than the latest
stored watermark, so rerunning the same input does not create duplicates.

## Current Behavior

The stock pipeline uses `pipeline_metadata` to track the latest processed
timestamp for each source and symbol.

Current flow:

1. Fetch stock data from Alpha Vantage.
2. Save the raw API response as JSON.
3. Parse the payload into database rows.
4. Read the previous watermark from `pipeline_metadata`.
5. Keep only rows newer than the watermark.
6. Upsert new rows into `market_bars`.
7. Update the watermark to the max timestamp from the loaded rows.

If there are no new rows, the pipeline exits without writing duplicates.

## Watermark Table

The watermark state is stored in `pipeline_metadata`.

Key fields:

- `source`: data source name, for example `alpha_vantage`
- `symbol`: entity being loaded, for example `AAPL`
- `last_watermark`: latest loaded timestamp
- `last_row_count`: number of rows loaded in the latest successful run
- `status`: latest run status
- `updated_at`: metadata update timestamp

## Idempotency Rule

The pipeline treats `(ts, symbol)` as the natural key for stock market bars.

`market_bars` has a primary key on:

```sql
(ts, symbol)
```

This gives the pipeline two layers of protection:

1. Incremental filtering only sends new rows to the load layer.
2. Database upsert prevents duplicate rows if the same data is loaded again.

## How to Verify

Start the database and apply migrations:

```bash
make db-up
make db-migrate
```

Run the stock pipeline:

```bash
make run
```

Run it a second time with the same available source data:

```bash
make run
```

Expected behavior:

- The first run loads new rows and updates `pipeline_metadata`.
- The second run should report no new rows when the watermark is current.
- `market_bars` row count should not increase for duplicate input.

Useful verification queries:

```sql
SELECT *
FROM pipeline_metadata
ORDER BY updated_at DESC;
```

```sql
SELECT symbol, COUNT(*) AS row_count
FROM market_bars
GROUP BY symbol
ORDER BY symbol;
```

## Test Coverage

Current coverage includes:

- `tests/unit/test_incremental.py`
  - verifies row filtering when no watermark exists
  - verifies only newer rows are kept
  - verifies empty output when no rows are newer
  - verifies max timestamp behavior for empty input
- `tests/smoke/test_pipeline_smoke.py`
  - verifies first load inserts rows
  - verifies watermark is updated
  - verifies a second load of the same rows does not duplicate data

## Backfill Plan

Full date-range backfill is planned for Week 10.

The intended backfill behavior is:

1. Accept `--start` and `--end` dates.
2. Validate the date range.
3. Process each date in order.
4. Reuse the same idempotent load path as the daily pipeline.
5. Resume safely from the stored checkpoint or watermark.

The current `scripts/backfill.py` is a scaffold and should not yet be treated
as a complete historical backfill runner.

## Current Limitations

- Backfill does not yet process date ranges.
- There is no separate checkpoint table beyond `pipeline_metadata`.
- Failure recovery is limited to rerunning the pipeline safely.
- Data quality checks are documented separately and are not yet enforced as
  blocking gates in the load path.
