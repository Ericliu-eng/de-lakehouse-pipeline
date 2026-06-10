# Weekly Log

## Week 01 — Repo Engineering Skeleton & MVP Pipeline
### Iteration 1 (2026-02-19) — Repo Foundation
**Deliverables**
- Set up repository skeleton (src/, data/, docs/)
- Implemented Makefile (setup / lint / test)
- Configured CI workflow (GitHub Actions)
- Added documentation (DEV_SETUP, STANDARDS, WEEKLY_LOG)
**Validation**
- `make setup`, `make lint`, `make test` all pass
- CI pipeline green


### Iteration 2 (2026-02-21) — MVP ETL Pipeline
**Deliverables**
- Implemented end-to-end ETL pipeline:
  - Extract: read `data/raw/sample.csv`
  - Transform: drop missing values, filter invalid rows
  - Load: write to `data/processed/output.csv`
- Updated README with run instructions
- Added execution proof under `docs/proof/`



### Iteration 3 (2026-02-21) — Unit Testing
**Deliverables**
- Refactored logic into `transform(df)`
- Added unit tests for:
  - normal cases
  - edge cases
  - failure cases
**Validation**
- `pytest` passes locally and in CI


### Iteration 4 (2026-02-21) — Smoke Test & CLI
**Deliverables**
- Implemented smoke (E2E) test using `tmp_path`
- Added Makefile commands:
  - `make run`
  - `make smoke`



### Iteration 5 (2026-02-21) — CI & Reproducibility
**Deliverables**
- CI pipeline fully passing (GitHub Actions)
- Improved README for reproducibility
- Added execution proof
**Validation**
- Fresh environment can reproduce results via:
  - `make setup`
  - `make test`
  - `make run`

### Iteration 6 (2026-02-22) — Demo Rehearsal
**Deliverables**
- Verified full pipeline using README instructions
- Ensured project is runnable by external users




# Week 01 Summary — Repo Engineering Skeleton & MVP Pipeline================================
## What I Completed
- Created the repository structure:
  - `src/`
  - `data/`
  - `docs/`
- Added basic engineering setup:
  - `Makefile`
  - GitHub Actions CI
  - README
  - development documentation
- Built the MVP ETL pipeline:
  - read data from `data/raw/sample.csv`
  - clean and filter invalid rows
  - save output to `data/processed/output.csv`
- Refactored the transform logic into a reusable function.
- Added tests:
  - unit tests
  - edge case tests
  - failure case tests
  - smoke test
- Added Makefile commands:
  - `make setup`
  - `make lint`
  - `make test`
  - `make run`
  - `make smoke`
- Added execution proof under `docs/proof/`.
## Validation
- `make setup` passed
- `make lint` passed
- `make test` passed
- `pytest` passed locally and in CI
- GitHub Actions CI pipeline passed



### W02D01 (2026-02-23) — Local Postgres + Migration Setup
**Deliverables**
- Set up local Postgres service using docker-compose
- Implemented DB connection module (`db.py`)
  - Config loading from environment variables
  - Connection handling via psycopg
  - DB readiness check (`wait_for_db`)
- Added migration and seed scripts:
  - `scripts/init_db.sql`
  - `scripts/seed.sql`
  - `scripts/migrate.py`
- Integrated DB workflow into Makefile:
  - `make db-up`
  - `make migrate`
- Added DB smoke test (`test_db_smoke.py`)
**Validation**
- Postgres container runs successfully via `docker compose up -d`
- Schema and seed data applied using `make migrate`
- DB smoke test validates:
  - Connection works
  - Table exists
  - Query returns expected results
- Full test suite passes locally (`make test`)


### W02D02 (2026-02-24) Postgres Data Stack + Testing (Unit + Integration)
**Deliverables**
- Completed Postgres-backed data workflow:
  - Docker Compose service (`db-up`, `db-down`)
  - Migration script (`scripts/migrate.py`) runs via module
  - Schema initialization (`init_db.sql`)
  - Seed data loading (`seed.sql`)
- Implemented testing layers:
  - DB smoke test (`tests/test_db_smoke.py`) verifies connectivity and query
  - Unit tests (`tests/test_db_unit.py`) for DB utilities:
    - Config loading (default + env override)
    - DSN generation
    - Timeout behavior (`wait_for_db`)
- Refactored Makefile:
  - Added `db-up`, `db-down`, `migrate`, `db-smoke`, `unit`
  - Standardized module execution (`-m`)
- Improved documentation:
  - README includes Local Postgres workflow
  - Reproducible commands clearly documented
- Added proof artifacts:
  - `docs/proof/2026-02-24_w02d2_full_run.txt`
  - `docs/proof/w02d2_w02d3_proof.txt`
**Validation**
- `make db-up` successfully starts Postgres container
- `make migrate` applies schema and seed without errors
- `make db-smoke` passes (DB reachable + query works)
- `make unit` passes (4/4 unit tests)
- `make test` passes all tests (9/9 total)
- Full workflow reproducible via Makefile commands


### W02D3 (2026-02-25) — DB Smoke Test + CI Alignment
**Deliverables**
- Implemented DB smoke test (`tests/test_db_smoke.py`)
- Verified:
  - Database connectivity
  - Table existence (`users`)
  - Seed data presence (Alice, Bob)
- Added helper function `_table_exists(conn, table_name)`
- Introduced pytest marker: `@pytest.mark.smoke`
- Registered marker in `pytest.ini`
- Refactored Makefile:
  - `db-smoke` runs pytest only (no docker in CI)

**Validation**
- Local:
  - Ran `make db-up` → Postgres container healthy
  - Ran `make migrate` → tables created + seed inserted
  - Ran `pytest -m smoke -vv` → PASSED
- CI:
  - Postgres provided via GitHub Actions `services`
  - Smoke test executed without docker compose
  - CI pipeline PASSED

### W02D04 (2026-02-26) — CI Integration + End-to-End Reproducibility
**Deliverables**
- Integrated Postgres workflow into CI (GitHub Actions)
- Standardized execution via Makefile (`setup`, `migrate`, `db-smoke`, `test`)
- Fixed Python import issue using editable install (`pip install -e .`)
- Improved README with clear Quickstart + DB workflow
- Added reproducible proof under `docs/proof/w02/2026-02-26-run.txt`
- Verified full pipeline runs from scratch (local)
**Validation**
- `make setup` successfully creates venv and installs dependencies
- `make db-up` starts Postgres container
- `make migrate` applies schema + seed without error
- `make run` processes data (4 → 2 rows) and writes output
- `make test` → 9 tests passed
- `make db-smoke` verifies DB connectivity + schema + seed
- CI pipeline runs: setup → lint → migrate → db-smoke → test

### W02D05 (2026-02-28) — Establish SQL Patterns, Data Quality Checks, and Initial SQL Tests
**Deliverables**
- Created/updated `docs/DATA_MODEL.md` describing the current schema and table fields.
- Added migration file `migrations/002_tables.sql` to support schema evolution (added `updated_at` column).
- Implemented SQL pattern library:
  - `sql/patterns_window.sql` — window function examples (`ROW_NUMBER`, dedup logic).
- Implemented data validation queries:
  - `sql/quality_checks.sql` — row count, null checks, duplicate detection.
- Added SQL smoke tests:
  - `tests/test_sql_queries.py` to verify SQL files execute correctly.
- Generated ERD placeholder diagram:
  - `docs/erd.png`.
- Recorded reproducibility proof:
  - `docs/proof/2026-02-28-run.txt`.
**Validation**
- Ran migrations successfully:
  - `make migrate`
- Verified code quality:
  - `make lint` (ruff checks passed).
- Executed tests:
  - `make test`
  - Smoke tests confirmed SQL queries run without errors.
- Confirmed CI workflow compatibility with migration + SQL checks.

# Week 02 Summary — Local Postgres + SQL Foundation ========================================
## What I Completed
- Set up local Postgres using Docker Compose.
- Added database workflow:
  - `db.py`
  - environment-based DB config
  - DB connection handling
  - DB readiness check with `wait_for_db`
- Added migration and seed workflow:
  - `scripts/init_db.sql`
  - `scripts/seed.sql`
  - `scripts/migrate.py`
  - `migrations/002_tables.sql`
- Updated Makefile commands:
  - `make db-up`
  - `make db-down`
  - `make migrate`
  - `make db-smoke`
  - `make unit`
  - `make test`
- Added DB testing:
  - DB smoke test
  - DB unit tests
  - SQL query tests
- Integrated Postgres into GitHub Actions CI.
- Fixed Python import issues using editable install:
  - `pip install -e .`
- Added SQL foundation:
  - `docs/DATA_MODEL.md`
  - `sql/patterns_window.sql`
  - `sql/quality_checks.sql`
  - `docs/erd.png`
- Added proof logs under:
  - `docs/proof/`
## Validation
- `make db-up` passed
- `make migrate` passed
- `make db-smoke` passed
- `make unit` passed
- `make test` passed
- `make lint` passed
- CI pipeline passed



### W03D01 (2026-03-04) — SQL Validation and Testing
**Deliverables**
- Executed SQL queries in `sql/patterns_window.sql`
- Verified deduplication logic using window functions
- Ran data quality checks from `sql/quality_checks.sql`
- Executed development workflow commands:
  - `make lint`
  - `make smoke`
- Recorded proof in 
**Validation**
- SQL queries executed successfully in local Postgres
- Lint checks passed
- Smoke tests confirmed database connectivity and query execution
- Workflow verified to be reproducible from command-line execution
- Proof log recorded under:
  - `docs/proof/2026-03-04-run.txt`


### W03D02 (2026-03-05) — SQL Utility Unit Tests
**Deliverables**
- Implemented SQL utility function tests for `split_sql_statements`
- Added unit test file: `tests/test_sql_utils.py`
- Implemented 4 unit tests:
  - `test_split_sql_statements_basic`
  - `test_split_sql_statements_removes_empty_fragments`
  - `test_split_sql_statements_strips_whitespace`
  - `test_split_sql_statements_empty_or_whitespace_input`
**Validaton**
- Ran lint check:
  - `make lint`
  - Result: All checks passed
- Ran unit tests:
  - `make sql-utils`
  - Result: 4 tests passed
- Proof log recorded under:
  - `docs/proof/2026-03-05-run.txt`


### W03D03 (2026-03-06) — Data Model Alignment & ERD
**Deliverables**
- Updated `docs/DATA_MODEL.md` to align with the current `users` table schema
- Added a simple ERD for the `users` table to visualize structure and relationships
- Ensured documentation reflects the latest schema fields (`id`, `name`, `created_at`, `updated_at`)
- Added proof record under `docs/proof/`
**Validation**
- Ran `make lint`
- Ran `make test`

### W03D4 (2026-03-07) — SQL Validation + Pipeline Smoke Test
**Deliverables**
- Ran full pipeline validation locally
- Verified CLI pipelines for:
  - Weather API ingestion
  - Stock (Alpha Vantage) ingestion
- Confirmed project passes linting and automated tests
**Validation**
Commands executed:
```bash
make lint
make db-up
make test
python -m src.de_lakehouse_pipeline.cli run_weather
python -m src.de_lakehouse_pipeline.cli run_daily
```

### W03D05 (2026-03-08) — Extraction Layer Core Logic
**Deliverables**
- Implemented API ingestion for external data sources
- Integrated stock data ingestion via `alpha_vantage_client.py`
- Integrated weather data ingestion via `weather_client.py`
- Connected ingestion flow into CLI commands:
  - `run_daily`
  - `run_weather`
- Implemented raw data landing using `save_raw_data()` with date-based folders
- Saved API responses as JSON files for downstream pipeline stages
**Validation**
- Successfully executed CLI commands locally
- Verified raw data files were created
- Ran project checks:
  - `make lint`
  - `make test`

# Week 03 Summary — Data Model + External API Ingestion=======================================
## What I Completed
- Updated `docs/DATA_MODEL.md` to match the current `users` table schema.
- Added a simple ERD for the `users` table.
- Documented the latest schema fields:
  - `id`
  - `name`
  - `created_at`
  - `updated_at`
- Ran local pipeline validation.
- Verified CLI pipeline commands for:
  - Weather API ingestion
  - Stock API ingestion
- Implemented external API ingestion logic:
  - `alpha_vantage_client.py`
  - `weather_client.py`
- Added CLI commands:
  - `run_daily`
  - `run_weather`
- Implemented raw data landing with `save_raw_data()`.
- Saved API responses as JSON files for later pipeline stages.
- Added proof records under:
  - `docs/proof/`
## Validation
- `make lint` passed
- `make test` passed
- `make db-up` ran successfully
- Weather ingestion CLI ran successfully
- Stock ingestion CLI ran successfully
- Raw JSON files were created locally


## W04D01(2026-03-9) — Extraction Unit Tests
**Deliverables**
- Implemented unit tests for `save_raw_data`
- Implemented edge tests for `fetch_current_weather`
- Verified error handling when API key is missing
**Validation**
- Ran `make lint`
- Ran `pytest tests/test_extraction.py`

## W04D02(2026-03-10) — Pipeline Smoke Test
---
**Deliverables**
- Implemented `test_pipeline_smoke`
- Used pytest `tmp_path` fixture to isolate test data
- Verified pipeline writes `raw/<date>/stock.json`
**Validation**
pytest output:
18 passed in X.XXs

## W04D03(2026-03-11) — Load Layer Scaffold for Weather Pipeline
---
**Deliverables**
- Implemented `test_pipeline_smoke`
- Implemented `test_pipeline_smoke`
- Connected weather CLI pipeline to run:
  - ingest → save raw → load → metadata → transform.
- Implemented simple weather transform output for end-to-end validation.
- Created proof artifact under `docs/proof/`.
**Validation**
- Successfully ran

### W04D03 (2026-03-12) — Introduced Database Load Layer for Market Data
**Deliverables**
- Created `market_bars` Postgres table with composite primary key `(ts, symbol)` for time-series storage.
- Implemented Alpha Vantage daily parser to convert nested API payload into relational row tuples.
  - ingest → raw landing → parse → load (upsert into Postgres)
**Validation**
Pipeline execution:
```bash
make db-up
make migrate
make run
```

# Week 04 Summary — Extraction Tests + Load Layer===========================================
## What I Completed
- Added unit tests for extraction logic:
  - `save_raw_data`
  - `fetch_current_weather`
  - missing API key error handling
- Added pipeline smoke test:
  - `test_pipeline_smoke`
  - used `tmp_path` to isolate test data
  - verified raw file output path:
    - `raw/<date>/stock.json`
- Connected the weather CLI pipeline flow:
  - ingest
  - save raw
  - load
  - metadata
  - transform
- Added simple weather transform output for end-to-end validation.
- Created the first Postgres load layer for market data:
  - created `market_bars` table
  - added composite primary key:
    - `(ts, symbol)`
- Implemented Alpha Vantage daily parser:
  - converted nested API response into relational rows
- Connected stock pipeline flow:
  - ingest
  - raw landing
  - parse
  - load into Postgres
- Added proof artifacts under:
  - `docs/proof/`
## Validation
- `make lint` passed
- `pytest tests/test_extraction.py` passed
- Pipeline smoke test passed
- `make db-up` ran successfully
- `make migrate` ran successfully
- `make run` executed the market data pipeline

## W005D01(2026-03-18) — Iimplement basic metadata tracking for stock load pipeline
**Deliverables**
- Implemented `metadata.py`,Used to generate a record of the current data loading operation.
- Implemented `metadata_writer.py` to insert load metadata records generated by `metadata.py` into the database.
**Validation**
Pipeline execution:
```bash
make db-up
make migrate
make run
```

## W005D02(2026-03-22) — Iimplement basic metadata tracking for stock load pipeline
**Deliverables**
- Implemented `test_market_data_client.py` include 6 unit test
- Implemented `test_loader.py` to test load layer ,include 1unit test
**Validation**
Pipeline execution:
```bash
make test
```

## W006D01(2026-03-23) — Implement basic metadata tracking for stock load pipeline
**Deliverables**
- Implemented `mart_daily_symbol_summary.py`
- Implemented `mart_symbol_latest_price.py` 
- Implemented `marts.mart_symbol_volume_rank.py` 
- Implemented `mart_daily_symbol_summary.sql` 
- Implemented `mart_symbol_latest_price.sql` 
- Implemented `marts.mart_symbol_volume_rank.sql` 
**Validation**
Pipeline execution:
```bash
    python -m de_lakehouse_pipeline.transform.marts.mart_daily_symbol_summary run
    python -m de_lakehouse_pipeline.transform.marts.mart_symbol_latest_price run
    python -m de_lakehouse_pipeline.transform.marts.mart_symbol_volume_rank run
```

## W006D02(2026-03-24) — Marts Layer Quality & Integration
**Deliverables**
- Implemented `test_marts.py`
**Validation**
```bash
make run-marts
```

### W006D03(2026-03-26) — feat/idempotency-incremental-processin
**Deliverables**
- `test_filter_new_rows_when_watermark_is_none`  unit test in `test_incremental.py`  
- `test_filter_new_rows_only_keeps_newer_rows` unit test in `test_incremental.py`
- `test_filter_new_rows_returns_empty_when_no_new_data` unit test in `test_incremental.py`
- `test_get_max_timestamp_empty`unit test in `test_incremental.py`
- `pipeline_metadata.py`have ges_last_watermark function and upsert watermark function
- `incremental.py` have filter_new_rows and get_max_timestamp functions
Pipeline execution:
```bash
make run
make test
```
# Week 06 Summary — Marts Layer + Incremental Processing====================================
## What I Completed
- Implemented marts Python modules:
  - `mart_daily_symbol_summary.py`
  - `mart_symbol_latest_price.py`
  - `mart_symbol_volume_rank.py`
- Implemented marts SQL files:
  - `mart_daily_symbol_summary.sql`
  - `mart_symbol_latest_price.sql`
  - `mart_symbol_volume_rank.sql`
- Added marts integration testing:
  - `test_marts.py`
- Added incremental processing logic:
  - `filter_new_rows`
  - `get_max_timestamp`
- Added pipeline metadata tracking:
  - `get_last_watermark`
  - `upsert_watermark`
- Added incremental unit tests:
  - watermark is `None`
  - only keeps newer rows
  - returns empty when no new data
  - max timestamp empty case
## Validation
- Marts ran successfully with:
  - `python -m de_lakehouse_pipeline.transform.marts.mart_daily_symbol_summary run`
  - `python -m de_lakehouse_pipeline.transform.marts.mart_symbol_latest_price run`
  - `python -m de_lakehouse_pipeline.transform.marts.mart_symbol_volume_rank run`
- `make run-marts` passed
- `make run` passed
- `make test` passed


## W009D01(2026-04-15) — backfill-range-backfill-resume
**Deliverables**
- `scripts/backfill.py`
- `tests/test_backfill.py`
- `docs/BACKFILL.md`
**Validation**
```bash
python scripts/backfill.py --start 2026-01-01 --end 2026-01-07
```

## W009D02(2026-04-16) — backfill-range-resume-from-checkpoint-runbook
**Deliverables**
- `scripts/backfill.py -Add simple checkpoint/resume behavior`
- `tests/test_backfill.py -Add simple checkpoint/resume behavior Test`
**Validation**
```bash
python scripts/backfill.py --start 2026-01-01 --end 2026-01-07
```

## W009D03(2026-04-19) — backfill-range-resume-from-checkpoint-runbook
**Deliverables**
- `quality/checks.py` add two function check_not_null  check_unique
- `unit/test_quality_checks.py` add two unit test for each function 
**Validation**
```bash
python -m pytest tests/unit/test_quality_checks.py   
```

# Week 09 Summary — Backfill + Quality Checks===============================================
## What I Completed
- Implemented backfill script:
  - `scripts/backfill.py`
- Added backfill tests:
  - `tests/test_backfill.py`
- Added backfill documentation:
  - `docs/BACKFILL.md`
- Added checkpoint/resume behavior to the backfill workflow.
- Updated backfill tests to cover checkpoint/resume behavior.
- Added basic quality check functions:
  - `check_not_null`
  - `check_unique`
- Added unit tests for quality checks:
  - not-null check test
  - unique check test
## Validation
- Backfill command ran successfully:
  - `python scripts/backfill.py --start 2026-01-01 --end 2026-01-07`
- Quality check unit tests passed:
  - `python -m pytest tests/unit/test_quality_checks.py`


## W010D01 (2026-04-23) — backfill-cli-integration
**Deliverables**
- Integrated `backfill` into the main CLI entrypoint.
- Added `backfill` as a supported CLI command.
- Added `--start` and `--end` arguments for date-range backfill.
- Wired the command flow:
  `cli.py -> backfill.py -> pipeline.py`
**Validation**
```bash
.venv/Scripts/python.exe -m de_lakehouse_pipeline.cli backfill --start 2026-04-16 --end 2026-04-16
```

## W011D01 (2026-05-02) — Data quality gates
**Deliverables**
- Added `check_freshness` function on `checks.py`
- Added `check_range` function on `checks.py`
- Added`test_check_range_passes_when_values_are_inside_range` func on `test_quality_checks.py`
- Added`test_check_range_fails_when_values_are_outside_range` func on `test_quality_checks.py`
- Added`test_check_freshness_passes_when_latest_data_is_recent` func on `test_quality_checks.py`
- Added`test_check_freshness_fails_when_latest_data_is_too_old` func on `test_quality_checks.py`
**Validation**
```bash
make test
```

## W14D01 (2026-05-19) — Fail and Edge Tests for Quality Checks
**Deliverables**
- Added `test_check_unique_fails_when_duplicates_exist()` in `test_quality_checks.py`
- Added `test_check_not_null_fails_when_null_rows_exist()` in `test_quality_checks.py`
- Added `test_check_range_raises_when_no_bounds_are_provided()` in `test_quality_checks.py`
**Validation**
```bash
make test
```
## W14D02 (2026-05-24) — Quality Checks Smoke Test
**Deliverables**
- Added `test_quality_checks_smoke_on_market_bars`
**Validation**
```bash
make test
```

## W015D01 (2026-05-28) — smoke-integration-tests-end-to-end-full
**Deliverables**
- Added`tests/smoke/test_pipeline_smoke/py`
**Validation**
```bash
make smoke
```

### W015D02 (2026-05-29) — orchestration-skeleton-reproducible-run
**Deliverables**
- Add a local orchestration skeleton for the stock pipeline `orchestration/dagster_pipeline.py`
- Define the intended pipeline execution order:
  - ingest raw stock data
  - load raw data to database
  - run transformations
  - run quality checks
  - build marts
- Add or verify `make orchestrate` command
**Validation**
```bash
make orchestrate
```

### W15D03A (2026-05-30) — lightweight orchestration metrics
**Deliverables**
- Added a lightweight metrics layer in `src/de_lakehouse_pipeline/metrics.py`
- Defined step-level metrics:
  - step name
  - status: success/failed
  - start time
  - end time
  - row count if available
  - error message if failed
- Defined pipeline-level metrics:
  - pipeline name
  - pipeline start time
  - pipeline end time
  - overall pipeline status
  - list of step metrics
- Simplified `orchestration/dagster_pipeline.py` into a clear sequential flow:
  - run stock pipeline
  - stop if stock pipeline fails
  - run quality checks
  - stop if quality checks fail
  - build marts
- Kept `run_step()` as the small wrapper for logging and metrics
- Updated operational documentation in `docs/OPS_METRICS.md`
- Updated orchestration documentation in `docs/ORCHESTRATION.md`

**Validation**
```bash
python -m pytest tests/unit/test_orchestration.py -v
```

### W15D03B (2026-05-30) — minimal S3 raw upload support
**Deliverables**
- Chose AWS S3 as the optional cloud raw storage target
- Defined raw object partition layout:
  - `raw/<source>/symbol=<symbol>/date=<YYYY-MM-DD>/<filename>`
  - example: `raw/alpha_vantage/symbol=AAPL/date=2026-05-30/stock.json`
- Added a minimal cloud storage module:
  - `src/de_lakehouse_pipeline/ingest/cloud_storage.py`
- Kept only the basic cloud storage behavior:
  - generate the raw S3 object key
  - skip upload by default
  - upload JSON when `ENABLE_S3_RAW_UPLOAD=true`
  - require `S3_RAW_BUCKET` only when upload is enabled
  - return the uploaded S3 URI string
- Integrated optional raw payload upload into the stock pipeline
- Added `boto3` dependency
- Added `make cloud-storage-test` command
- Updated docs:
  - `docs/CLOUD_STORAGE.md`
  - `README.md`

**Validation**
```bash
python -m pytest tests/unit/test_cloud_storage.py -v
python -m pytest tests/unit -v
```

### W15D03C (2026-05-30) — terraform-scaffold
**Deliverables**
- infra/terraform/main.tf
- infra/terraform/variables.tf
- infra/terraform/outputs.tf
- infra/terraform/README.md

# Week 15 Summary — Smoke Tests + Orchestration + Metrics + Cloud Storage + Terraform===========
## What I Completed
- Added end-to-end smoke integration test:
  - `tests/smoke/test_pipeline_smoke.py`
- Added local orchestration skeleton:
  - `orchestration/dagster_pipeline.py`
- Defined the intended pipeline execution order:
  - ingest raw stock data
  - load raw data to database
  - run transformations
  - run quality checks
  - build marts
- Added or verified orchestration command:
  - `make orchestrate`
- Added lightweight orchestration metrics:
  - `src/de_lakehouse_pipeline/metrics.py`
- Added step-level metrics:
  - step name
  - status: success / failed
  - start time
  - end time
  - row count if available
  - error message if failed
- Added pipeline-level metrics:
  - pipeline name
  - pipeline start time
  - pipeline end time
  - overall pipeline status
  - list of step metrics
- Simplified orchestration flow in:
  - `orchestration/dagster_pipeline.py`
- Kept `run_step()` as the small wrapper for logging and metrics.
- Updated operational documentation:
  - `docs/OPS_METRICS.md`
- Updated orchestration documentation:
  - `docs/ORCHESTRATION.md`
- Added minimal S3 raw upload support:
  - `src/de_lakehouse_pipeline/ingest/cloud_storage.py`
- Chose AWS S3 as the optional cloud raw storage target.
- Defined raw object partition layout:
  - `raw/<source>/symbol=<symbol>/date=<YYYY-MM-DD>/<filename>`
  - example: `raw/alpha_vantage/symbol=AAPL/date=2026-05-30/stock.json`
- Implemented basic cloud storage behavior:
  - generate the raw S3 object key
  - skip upload by default
  - upload JSON when `ENABLE_S3_RAW_UPLOAD=true`
  - require `S3_RAW_BUCKET` only when upload is enabled
  - return the uploaded S3 URI string
- Integrated optional raw payload upload into the stock pipeline.
- Added `boto3` dependency.
- Added cloud storage test command:
  - `make cloud-storage-test`
- Updated cloud storage documentation:
  - `docs/CLOUD_STORAGE.md`
  - `README.md`
- Added Terraform scaffold:
  - `infra/terraform/main.tf`
  - `infra/terraform/variables.tf`
  - `infra/terraform/outputs.tf`
  - `infra/terraform/README.md`
## Validation
- Smoke integration test ran successfully:
  - `make smoke`
- Local orchestration command ran successfully:
  - `make orchestrate`
- Orchestration unit tests passed:
  - `python -m pytest tests/unit/test_orchestration.py -v`
- Cloud storage unit tests passed:
  - `python -m pytest tests/unit/test_cloud_storage.py -v`
- Full unit test suite passed:
  - `python -m pytest tests/unit -v`


### W16D01 (2026-06-01) — terraform-scaffold
**Deliverables**
- Add one failure test for `upload_raw_payload_if_enabled`
- Add one edge-case test for `ENABLE_S3_RAW_UPLOAD`


### W16D02 (2026-06-02) - Cloud storage smoke test
**Deliverables**
- Added lightweight cloud storage smoke test for S3 raw upload path.
- Verified cloud storage unit and smoke tests.
- Confirmed CI already runs the cloud storage unit test path.


### W16D03 (2026-06-06) - Terraform AWS apply and clean destroy
**Deliverables**
- Configured AWS credentials locally and confirmed Terraform can connect to AWS.
- Ran `terraform init` successfully and installed the AWS provider.
- Ran `terraform plan` successfully with `raw_bucket_name=eric-lakehouse-raw-dev-20260601`.
- Ran `terraform apply` and created 2 AWS resources:
  - `aws_s3_bucket.raw`
  - `aws_iam_policy.raw_writer`
- Verified Terraform outputs:
  - `raw_bucket_name`
  - `raw_bucket_arn`
  - `raw_writer_policy_arn`
- Ran `terraform destroy` and removed both AWS resources cleanly.
- Confirmed Week 16 Terraform workflow works end-to-end: `plan -> apply -> outputs -> destroy`.


### W16D04 (2026-06-07) Reliability drill flow
**Deliverables**
- Added reliability drill documentation in `docs/FAILURE_DRILLS.md`.
- Added retryable API status code behavior for API failure handling.
- Treated `429`, `500`, `502`, `503`, and `504` as retryable API errors.
- Treated `400` as a non-retryable API error.
- Added schema validation for required stock row fields.
- Added DB write safety logic so watermark updates only after successful load.
- Added unit tests for reliability drill logic.
- Added a smoke test for the reliability drill path.


# Week 16 Summary — Cloud Storage Tests + Terraform AWS Workflow + Reliability Drills
## What I Completed
### 1. Cloud Storage Reliability Tests
- Added failure test coverage for `upload_raw_payload_if_enabled`.
- Added edge-case test coverage for `ENABLE_S3_RAW_UPLOAD`.
- Verified that S3 upload behavior is safe by default:
  - upload is skipped unless explicitly enabled
  - `S3_RAW_BUCKET` is only required when upload is enabled
  - failure cases are tested
### 2. Cloud Storage Smoke Test
- Added a lightweight cloud storage smoke test for the S3 raw upload path.
- Verified both cloud storage unit tests and smoke tests.
- Confirmed CI already runs the cloud storage unit test path.
### 3. Terraform AWS End-to-End Workflow
- Configured AWS credentials locally.
- Confirmed Terraform can connect to AWS.
- Ran Terraform workflow successfully:
- Created and verified 2 AWS resources during `terraform apply`:
  - `aws_s3_bucket.raw`
  - `aws_iam_policy.raw_writer`
- Ran `terraform destroy` and removed all AWS resources cleanly.
### 4. Reliability Drill Flow
- Added reliability drill documentation:
  - `docs/FAILURE_DRILLS.md`
- Added retryable API error behavior:
  - retryable: `429`, `500`, `502`, `503`, `504`
  - non-retryable: `400`
- Added schema validation for required stock row fields.
- Added DB write safety logic:
  - watermark updates only after successful load
  - failed loads should not advance pipeline state
- Added unit tests for reliability drill logic.
- Added smoke test coverage for the reliability drill path.
- Updated verification commands and proof output for Week 16 reliability work.

## Validation
```bash
python -m pytest tests/unit/test_cloud_storage.py -v
python -m pytest tests/unit -v
make smoke
make orchestrate
terraform init
terraform plan
terraform apply
terraform destroy
```


### W17D01 Dashboard / Serving: Minimal Visualization and Query API
**Deliverables**
- Added `serve/api.py` with:
  - `health()`
  - `latest_price()`
  - `dashboard()`
- Added `serve/templates/dashboard.html`
- Added unit tests for `serve/api.py`, including:
  - `test_health`
  - `test_latest_price`
  - `test_dashboard_returns_html`
- Added smoke tests for the serving/dashboard path, including:
  - `test_health_endpoint_returns_ok`
  - `test_latest_price_endpoint_returns_expected_shape`
  - `test_dashboard_app_file_exists`
  - `test_dashboard_app_contains_expected_title`


### W17D02   Architecture Docs and Database-Backed Serving API
**Deliverables**
- Added `docs/ARCHITECTURE.md` to document the end-to-end system flow:
  - Alpha Vantage ingestion
  - raw JSON landing
  - staging transform
  - Postgres warehouse tables
  - incremental watermark tracking
  - data quality checks
  - analytical marts
  - FastAPI serving/dashboard
- Added `docs/RUNBOOK.md` with local run commands, validation commands, database inspection queries, troubleshooting steps, and proof checklist.
