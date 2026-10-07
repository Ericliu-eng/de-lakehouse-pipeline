# Failure Drills

## Purpose

These drills document how the pipeline should respond to common production
failures and distinguish verified safeguards from remaining gaps.

| Drill | Expected safeguard | Current evidence | Remaining gap |
| --- | --- | --- | --- |
| API rate limit or server error | Retry transient failures, fail clearly, and avoid partial writes | Request-path tests cover 429/500/502/503/504 recovery, retry exhaustion, and immediate failure on 400/401/403/404 | Retry-After handling and orchestration-level retries are not implemented |
| Upstream schema change or invalid values | Preserve raw data and reject malformed OHLCV before writes | Both source staging paths call the shared validator; tests reject null/missing fields, non-finite/negative prices, inconsistent OHLC, fractional volume, and future dates before DB access | Historical corrections need an explicit reprocess mode |
| Invalid existing warehouse rows | Prevent publication through manual and orchestrated commands | Real PostgreSQL tests reject invalid rows before manual mart builds; existing marts remain unchanged | Concurrent writes between validation and publication are not coordinated |
| Database write failure | Roll back facts, watermark, and load metadata together | `tests/integration/test_pipeline_transactions.py` injects a PostgreSQL constraint failure at audit insertion for both normal loading and backfill, then checks rollback and retry recovery | Requires PostgreSQL; concurrent-run coordination is not covered |

## Drill Details

### API Failure

Retryable conditions include timeouts, connection failures, HTTP `429`, and
HTTP `500`, `502`, `503`, and `504` responses. Retries use a finite retry budget
and exponential backoff. Invalid
requests and authentication failures should fail without retrying.

### Schema Change

Missing or invalid required market fields must stop the load. Additional fields
may be ignored when they do not change the required schema. The preserved raw
payload provides evidence for debugging and replay.

### Database Failure

A failed fact-table write must not advance incremental state. Fact rows,
watermark state, and load metadata are committed as one atomic transaction by
the pipeline connection context. Writers do not commit independently.

## Validation

Run automated reliability checks:

```bash
make unit
make smoke
```

Validate the database environment:

```bash
make db-up
make db-migrate
make smoke-db
make integration
```

The remaining gaps require integration tests with explicit failure injection
before they can be treated as production guarantees.
