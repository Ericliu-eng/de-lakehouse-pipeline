# Incremental Loading

## Overview

The stock pipeline uses watermark-based incremental loading so routine reruns
process only newer market bars without creating duplicates.

## Incremental State

State is stored in `pipeline_metadata`, keyed by `(source, symbol)`.

| Column | Purpose |
| --- | --- |
| `last_watermark` | Latest successfully processed market timestamp |
| `last_row_count` | Rows processed in the latest successful load |
| `status` | Latest persisted load status |
| `updated_at` | Metadata update timestamp |

## Load Flow

```text
Fetch API payload
  -> Preserve raw JSON
  -> Transform typed rows
  -> Read watermark
  -> Filter newer rows
  -> Upsert market_bars
  -> Update watermark and load metadata
```

Fact rows, watermark, and load audit commit together on the pipeline connection;
an audit failure rolls back all three. The watermark advances only after the
market-bar upsert succeeds. If the same
payload runs again, no rows pass the watermark filter and the fact-table row
count remains stable.

## Idempotency Controls

- Watermark filtering skips timestamps processed by routine runs.
- `market_bars` uses `(ts, symbol)` as its primary key.
- Database writes use upsert semantics rather than append-only inserts.

An empty incremental run exits without changing the watermark or writing a new
load metadata record.

## Backfill and Late Data

The date-range backfill bypasses routine watermark filtering to insert missing
historical dates:

```bash
make backfill START=2026-04-16 END=2026-04-18 SYMBOL=AAPL
```

Dates already present for the source and symbol are skipped. A force-correction
mode is not implemented. The per-date writer uses primary-key upserts, but the
range command does not call it for existing dates. The stored watermark becomes the greater of
the existing watermark and the maximum backfilled timestamp, preventing state
from moving backward. Checkpoints support safe resume behavior; see
`docs/BACKFILL.md`.

## Validation

```bash
make unit
make db-up
make db-migrate
make smoke-db
```

The incremental smoke test verifies duplicate prevention and stable watermark
behavior on repeated timestamps.

## Known Limitations

- Empty and failed runs are not persisted as pipeline metadata events.
- Routine loads and the default backfill cannot correct existing historical
  rows. A future force-reprocess mode needs explicit overwrite semantics.
- Concurrent runs are not coordinated; run ingestion and mart publication
  serially. Atomic writes alone do not prevent competing watermark updates or
  shared raw-file overwrites.
- One watermark is maintained for each `(source, symbol)` pair.
