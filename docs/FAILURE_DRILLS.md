# Failure Drills

## Purpose

These drills document how the pipeline should respond to common production
failures and distinguish verified safeguards from remaining gaps.

| Drill | Expected safeguard | Current evidence | Remaining gap |
| --- | --- | --- | --- |
| API rate limit or server error | Retry transient failures, fail clearly, and avoid partial writes | Timeout, connection, and Alpha Vantage `Note` retries are tested; retryable HTTP status codes are classified | HTTP `429` and `5xx` exceptions are not yet connected to the retry loop |
| Upstream schema change | Preserve raw data and reject malformed required fields | Raw JSON is saved before transformation; missing-field validation is tested | The dedicated schema validator is not yet called by the main pipeline |
| Database write failure | Roll back uncommitted writes and do not advance the watermark after a failed fact load | Fact loading runs before the watermark update; watermark safety behavior is tested | No real database failure is injected, and load operations are not yet one atomic transaction |

## Drill Details

### API Failure

Retryable conditions include timeouts, connection failures, HTTP `429`, and
HTTP `5xx` responses. Retries should use bounded exponential backoff. Invalid
requests and authentication failures should fail without retrying.

### Schema Change

Missing or invalid required market fields must stop the load. Additional fields
may be ignored when they do not change the required schema. The preserved raw
payload provides evidence for debugging and replay.

### Database Failure

A failed fact-table write must not advance incremental state. Fact rows,
watermark state, and load metadata should ultimately be committed as one atomic
transaction.

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
```

The remaining gaps require integration tests with explicit failure injection
before they can be treated as production guarantees.
