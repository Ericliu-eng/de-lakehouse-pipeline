# Backfill Strategy 

## Goal
Enable rerunning pipeline for historical dates without duplication.

## Concepts
- Watermark: last processed timestamp
- Idempotency: same run produces same result

## TODO
- Filter rows > watermark
- Backfill date ranges