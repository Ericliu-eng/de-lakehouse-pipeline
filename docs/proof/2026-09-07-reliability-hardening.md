# Reliability hardening validation

Date: 2026-09-07

## Changes verified

- Backfill checkpoints are scoped by source and normalized symbol. Database
  reconciliation prevents stale or legacy checkpoint dates from hiding missing
  rows. File replacement is atomic.
- Fact rows, watermark, and load metadata share the pipeline transaction.
- The CLI prints failure metrics and exits with status 1 after any failed step.
- HTTP 429/500/502/503/504 retry within the configured budget; permanent HTTP
  errors fail immediately.
- `make test`, and therefore the existing CI job, now includes database smoke
  tests. Database validation setup includes migration and seeding.

## Local results

- `python -B -m pytest tests/unit tests/smoke -m "not db" -p no:cacheprovider -q`:
  **104 passed, 6 deselected**.
- `python -B -m ruff check . --no-cache`: **All checks passed**.
- After `python -B -m scripts.migrate` and `python -B -m scripts.seed_db`,
  `python -B -m pytest tests -p no:cacheprovider -q`: **119 passed**.

The full suite used a temporary PostgreSQL 16 container, bound to loopback with
an ephemeral host port and no project data volume. No live market-data API was
called. The new transaction tests use unique schemas and a real PostgreSQL
CHECK constraint to reject audit insertion, then verify that all three tables
remain empty and a retry commits all three records. Both routine loading and
date backfill are covered. This records local verification, not a GitHub CI run.
