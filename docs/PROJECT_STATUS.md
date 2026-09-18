# Project Status and Completion Plan

Last reviewed: 2026-09-17

## Executive Status

The repository demonstrates a complete local data-engineering path: API
ingestion, raw retention, typed staging, PostgreSQL loading, incremental state,
quality gates, analytical marts, orchestration, serving, tests, CI, and an
infrastructure scaffold. It is a strong portfolio project, but three verified
production-path gaps should be fixed before calling it resume-ready.

## Verified Today

| Check | Result | Evidence |
| --- | --- | --- |
| Unit tests | 94 passed | `.venv/Scripts/python.exe -m pytest tests/unit -q` |
| Static analysis | Passed | `.venv/Scripts/python.exe -m ruff check .` |
| CI definition | Present | `.github/workflows/ci.yml` |
| PostgreSQL integration coverage | Present, not rerun in this review | `tests/integration/` and DB smoke tests |
| Terraform validation in CI | Configured, not rerun in this review | `make terraform-validate` in CI |

Do not interpret this table as proof that the live Alpha Vantage, AWS, or full
database-backed path ran successfully on this date. New proof belongs under
`docs/proof/` and should include the exact command, result, date, and relevant
environment assumptions without including secrets.

## Release Blockers

### P0 - Make enabled S3 upload executable

`run_stock()` and `run_stock_for_date()` call
`upload_raw_payload_if_enabled()` without an `s3_client`. When
`ENABLE_S3_RAW_UPLOAD=true`, the adapter requires that client and raises
`CloudStorageConfigError`. Unit tests pass because they inject a fake client
directly into the adapter; they do not prove the main pipeline path.

Definition of done:

- the runtime creates or receives an S3 client when upload is enabled;
- disabled upload remains dependency-free and safe by default;
- one test executes the main pipeline with upload enabled and a fake client;
- `docs/CLOUD_STORAGE.md` contains the exact runtime configuration and failure
  behavior.

### P0 - Scope freshness to the data being published

`check_freshness()` currently calculates `MAX(ts)` over all of `market_bars`.
A fresh AAPL row can therefore hide stale MSFT data. The check should accept
filters (at minimum `source` and `symbol`) or run grouped checks and fail when
any required partition is stale.

Definition of done:

- freshness cannot be satisfied by an unrelated symbol or source;
- tests cover one fresh and one stale symbol in the same table;
- orchestration passes the active source/symbol context to the gate;
- the documented 14-day threshold matches the implemented behavior.

### P0 - Put schema validation on the production path

`quality/schema_validation.py` defines and tests required fields, but staging
does not call it. Connect validation to the boundary where source records are
converted into typed rows, and add a failure-path test using a malformed source
record.

Definition of done:

- malformed records fail before a database write;
- the error identifies the missing or invalid field;
- the production-path test proves the validator was invoked.

## What To Do Today

Keep today's scope to one reviewable pull request that closes the three P0
items. Suggested order:

1. Write failing production-path tests for S3 client injection, per-symbol
   freshness, and malformed source records.
2. Implement the smallest fixes needed to make those tests pass.
3. Run `make lint` and `make unit`; then start PostgreSQL, migrate, and run
   `make test` if Docker is available.
4. Capture the commands and results in a dated `docs/proof/` note.
5. Update this file by moving completed items to the verified table and open a
   pull request with the CI result linked.

Avoid adding Spark, Snowflake, Airflow, or dbt today. Those are useful only
after this repository's existing execution path is demonstrably correct.

## Next After The P0 Fixes

1. Record one clean-clone setup and a two-to-four-minute demo path.
2. Add screenshots of the mart queries and serving dashboard.
3. Tag `v1.0.0` and publish a GitHub release with a short changelog.
4. Consider a `pipeline_runs` history table and persisted SLA metrics as a
   post-v1 reliability extension.

## Resume-Ready Exit Criteria

- all three P0 issues above are closed by tests on the real execution path;
- local full-suite and GitHub CI results are recorded;
- the README quickstart works from a clean clone;
- a short demo shows ingest -> quality gate -> marts -> serving;
- release `v1.0.0` points to the verified commit.
