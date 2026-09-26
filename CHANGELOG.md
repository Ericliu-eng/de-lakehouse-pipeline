# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/).

## [1.1.0] — 2026-09-25

Hardens the pipeline's correctness and failure handling, adds decades of price
history from a second source, and records measured results.

### Added

- **Tiingo history backfill** (`make tiingo-backfill SYMBOL=AAPL,MSFT`): loads
  full daily history in one request per symbol. The backfill is insert-only on
  `(ts, symbol)`, so Alpha Vantage daily rows are never overwritten. It
  normalizes Tiingo's UTC-midnight dates to the warehouse's US/Eastern grain,
  reconciles closes on overlapping days, and writes rows, watermark, and audit
  in one transaction. A live run added 97,057 bars for 10 symbols (1970–2026);
  1,219 overlapping days matched Alpha Vantage closes.
- **Offline benchmark** (`make benchmark`): replays saved payloads into a
  throwaway database and reports incremental loading, idempotent reruns,
  transactional rollback, backfill crash recovery, the quality gate, API retry
  behavior, and end-to-end latency. With saved Tiingo payloads it also measures
  the full-history warehouse: 97,276 rows backfilled in 7.2 s, 60 quality
  checks in 0.4 s, a 1.0 s mart rebuild, and a 15.3 s daily 10-symbol run.
- **Coverage reporting** (`make coverage`): 159 tests, 85% line coverage of
  `src/` and `orchestration/`.
- Production S3 upload path for raw payloads, with bucket encryption,
  versioning, and ownership controls in Terraform.
- CSV export of `market_bars`.
- Data contract, data model, and schema evolution documentation.
- Proof records for the fresh-clone quickstart and the demo mart query
  results; `docs/PROJECT_STATUS.md` is now the single status document.

### Changed

- Freshness checks are scoped to the active `(source, symbol)`, so one fresh
  symbol can no longer hide a stale one.
- Schema validation runs on the production staging path, before any warehouse
  write.
- Date-range backfill fetches the provider payload once and reuses it for
  every pending date instead of calling the API per day.
- Backfill checkpoints are scoped by source and symbol, reconciled with the
  database, and replaced atomically.
- Fact rows, watermark, and load audit share one transaction.
- HTTP 429/500/502/503/504 are retried within a bounded budget; permanent HTTP
  errors fail immediately. The orchestration CLI exits non-zero after a failed
  step.
- Ruff is pinned and the lint configuration is explicit.

### Fixed

- Broken screenshot links in the W17 proof and a misnamed `.txy` proof file.

### Removed

- The unreferenced `transform_stock` module.

### Tests

- Real PostgreSQL rollback tests after a rejected audit write, for both routine
  loading and backfill.
- Unit tests for CLI dispatch and in-process Dagster job execution.
- Integration tests for the Tiingo backfill: no overwrite, zero-row rerun,
  reconciliation counts, and rollback.
- Verified from a fresh clone: `make setup`, migrations, seeding, `make lint`,
  and `make test` (157 tests) against PostgreSQL 16.

## [1.0.0] — 2026-06-20

Initial release: Alpha Vantage extraction with retries, raw landing,
incremental PostgreSQL loading with watermarks, resumable backfill, quality
gates, three analytical marts, FastAPI serving, Dagster orchestration, CI, and
Terraform-managed S3 storage.

[1.1.0]: https://github.com/Ericliu-eng/de-lakehouse-pipeline/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/Ericliu-eng/de-lakehouse-pipeline/releases/tag/v1.0.0
