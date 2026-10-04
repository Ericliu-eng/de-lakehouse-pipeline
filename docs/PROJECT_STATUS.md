# Project Status and Completion Plan

Last reviewed: 2026-10-04 (after v1.1.0 and the PipeGuard integration)

This file is the single source of truth for project status. It supersedes the
earlier completion checklist v2, the Improvement Plan, and the 2026-09-17
completion plan; their remaining items are merged below.

## Executive Status

The pipeline is complete end to end on PostgreSQL with two sources: Alpha
Vantage for daily incremental loads and Tiingo for a one-off history backfill
(98,276 bars for 10 symbols, 1970–2026). The three production-path gaps found
on 2026-09-17 are closed, measured results are recorded, and the quickstart
passes from a fresh clone.

The project is resume-ready. The Alpha Vantage key that appeared in early
commit history has been rotated, v1.1.0 is tagged and released, and the README
carries an animated walkthrough of the data flow. A live screen recording
remains optional.

## Verified

| Check | Result | Evidence |
| --- | --- | --- |
| Static analysis | Passed | `python -m ruff check .` |
| Fresh-clone quickstart | `make test`: 157 passed | [Clean clone](proof/2026-09-25-clean-clone.md) |
| Full suite and coverage | 220 passed; 88% line coverage (2026-10-04) | `make coverage` on a freshly migrated database |
| GitHub CI on `main` | Success at `1ee070e` | [CI run](https://github.com/Ericliu-eng/de-lakehouse-pipeline/actions/runs/36215319646) |
| Benchmark | Full-history scale plus correctness and recovery scenarios | [Benchmark](proof/2026-09-25-benchmark.md) |
| Live Tiingo backfill | 97,057 rows added; 1,219 overlapping days, 0 beyond 0.5% | [Tiingo backfill](proof/2026-09-25-tiingo-backfill.md) |
| Demo mart queries | Results recorded | [Mart queries](proof/2026-09-25-mart-queries.md) |

## Closed Since 2026-09-17

| Item | Resolution |
| --- | --- |
| S3 upload not executable when enabled | Runtime creates a boto3 client when none is supplied (#78) |
| Freshness satisfied by unrelated symbols | Freshness is scoped to the active `(source, symbol)` (#80) |
| Schema validator off the production path | Staging validates required fields before warehouse writes (#81) |
| No measured results | Offline benchmark (#83), extended to the full-history warehouse in v1.1.0 |
| No coverage figure | `make coverage`; 74% → 85% (#84–#86) |
| CLI and Dagster job untested | 0% → 95% and 100% (#85) |
| Only about 100 days of history | Insert-only Tiingo backfill with cross-source reconciliation (#86) |
| Idempotent rerun and interrupted backfill not demonstrated | Benchmark sections 1 and 3: 0 new rows on rerun; crash after 4 of 9 days resumes with 0 gaps |
| No CHANGELOG; release predates fixes | [CHANGELOG](../CHANGELOG.md) and v1.1.0 |
| Quickstart unverified from a clean clone | Verified; Windows long-path issue documented in [DEV_SETUP](DEV_SETUP.md) |
| Demo query results missing | Recorded as text output rather than screenshots |
| CI badge, ERD, data contract, schema evolution | Present in README, [DATA_MODEL](DATA_MODEL.md), [DATA_CONTRACT](DATA_CONTRACT.md), [SCHEMA_EVOLUTION](SCHEMA_EVOLUTION.md) |
| FK check scope undocumented | [DATA_QUALITY](DATA_QUALITY.md) explains why it is not part of the gate |
| Live S3 upload unproven | [Live upload and read-back](proof/2026-09-30-s3-live-upload.md): payload identical to the local raw file; Moto and `terraform test` in CI |
| Proof typos | `W10/2026-04-23-run.txy` renamed to `.txt`; W17 screenshot links fixed |

## Open Items

### Optional

- Record a two-to-four-minute live demo: ingest -> quality gate -> marts ->
  serving, plus the history backfill and benchmark results.

### Engineering

- Rebuild marts once per batch, or incrementally, instead of once per symbol.
  At 98k rows the rebuild is 91% of a 15.3 s daily 10-symbol run.
- Persist step details for each `pipeline_runs` record, add a failure-rate
  query, and wire the SLA helpers to it.
- Route the Dagster scheduled job through the same run recording and PipeGuard
  reporting as the CLI runner.
- Rework `mart_daily_symbol_summary`: with one bar per symbol and day, its
  average, minimum, and maximum close are identical. Use the daily high-low
  range or a weekly or monthly rollup.
- Add a force-reprocess option for historical date corrections.
- Optionally store adjusted prices; both sources load unadjusted OHLCV, so
  splits appear as price jumps.
- dbt staging and mart models with tests, released as v1.2.0.

### Evidence

- Add a compatibility test that upgrades a populated older schema.
- Raise coverage for the CSV export and `checkdb` (0%) and the serving API
  (70%).

## Resume-Ready Exit Criteria

| Criterion | Status |
| --- | --- |
| Historical API key rotated | Done (2026-10-04) |
| README quickstart works from a clean clone | Done |
| Full-suite and CI results recorded for the release commit | Done for `1ee070e` |
| Measured results in the README | Done |
| Demo in the README | Done (animated walkthrough); live recording optional |
| Release points to the verified commit | Done (v1.1.0) |

## Ground Rules

- Every number and tool name on a resume or in the README must trace to code
  or a proof file in this repository.
- No Spark, Snowflake, Airflow, or Delta Lake unless a target role requires
  them. dbt is named only after it is in the repository.
