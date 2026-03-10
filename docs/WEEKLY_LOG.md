# Weekly Log
## Template
## Week <W> — <Topic>
### W<WW>D<D> (<YYYY-MM-DD>)— <Title>
**Deliverables** 
...
**Validation**
...
**Challenges**
...
**Fixes**
...
**Outcome**
...

## Week 01 — Repo Engineering Skeleton & MVP Pipeline
### Iteration 1 (2026-02-19) — Repo Foundation-----------------------------
**Deliverables**
- Set up repository skeleton (src/, data/, docs/)
- Implemented Makefile (setup / lint / test)
- Configured CI workflow (GitHub Actions)
- Added documentation (DEV_SETUP, STANDARDS, WEEKLY_LOG)
**Validation**
- `make setup`, `make lint`, `make test` all pass
- CI pipeline green
**Next**
- Implement minimal ETL pipeline

### Iteration 2 (2026-02-21) — MVP ETL Pipeline------------------------
**Deliverables**
- Implemented end-to-end ETL pipeline:
  - Extract: read `data/raw/sample.csv`
  - Transform: drop missing values, filter invalid rows
  - Load: write to `data/processed/output.csv`
- Updated README with run instructions
- Added execution proof under `docs/proof/`
**Validation**
- Pipeline runs successfully via CLI
- Output file generated correctly
**Challenges**
- Module import issue (`de_lakehouse_pipeline`)
- Fixed using module execution (`python -m`)
**Next**
- Add unit tests

### Iteration 3 (2026-02-21) — Unit Testing----------------------------
**Deliverables**
- Refactored logic into `transform(df)`
- Added unit tests for:
  - normal cases
  - edge cases
  - failure cases
**Validation**
- `pytest` passes locally and in CI
**Key Insight**
- Separated business logic (transform) from orchestration (main)
**Next**
- Add smoke / E2E test

### Iteration 4 (2026-02-21) — Smoke Test & CLI----------------------------
**Deliverables**
- Implemented smoke (E2E) test using `tmp_path`
- Added Makefile commands:
  - `make run`
  - `make smoke`
**Validation**
- One command runs pipeline end-to-end
**Challenges**
- Import issue due to `src/` structure
- Refactored entry point (`run_pipeline`)
**Next**
- Ensure reproducibility and CI integration

### Iteration 5 (2026-02-21) — CI & Reproducibility---------------------------------
**Deliverables**
- CI pipeline fully passing (GitHub Actions)
- Improved README for reproducibility
- Added execution proof
**Validation**
- Fresh environment can reproduce results via:
  - `make setup`
  - `make test`
  - `make run`

### Iteration 6 (2026-02-22) — Demo Rehearsal--------------------------------
**Deliverables**
- Verified full pipeline using README instructions
- Ensured project is runnable by external users
**Validation**
- End-to-end pipeline runs in <2 minutes
- No missing steps or hidden dependencies
**Outcome**
- Project is now reproducible, testable, and demo-ready


# Week 01 Summary------------------------------------------------------

### System Capability
- Reproducible ETL pipeline (CLI + Makefile)
- Deterministic data transformation layer
- CI-validated test suite (unit + smoke)
- Cross-platform support (Windows + Linux CI)

### Engineering Guarantees
- Reproducibility: fresh setup works via `make setup`
- Testability: unit + E2E coverage
- Isolation: business logic decoupled from IO
- Automation: CI enforces correctness

### Metrics
- CI passing (GitHub Actions)
- Runtime: <2 minutes end-to-end
- Test coverage: basic unit + smoke coverage
- Output correctness validated

### Gaps / Next Risks
- No persistent storage (currently file-based)
- No logging / observability
- No schema enforcement
- No configuration layer (.env not fully utilized)



### W02D1 (2026-02-23) — Local Postgres + Migration Setup---------------------------

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

**Challenges**
- Import issues with `src/` layout (`ModuleNotFoundError`)
- Missing dependency (`psycopg`) during initial setup
- CI environment lacks Postgres service, causing test failure

**Fixes**
- Added `export PYTHONPATH := src` in Makefile
- Installed `psycopg[binary]` in requirements.txt
- Updated DB smoke test to skip when Postgres is not available

**Outcome**
- Local data stack (Postgres + migration + seed) fully operational
- Database layer integrated into pipeline workflow
- Project now supports both file-based and DB-backed workflows

### W02D2 (2026-02-24) Postgres Data Stack + Testing (Unit + Integration)---------
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

---

**Validation**
- `make db-up` successfully starts Postgres container
- `make migrate` applies schema and seed without errors
- `make db-smoke` passes (DB reachable + query works)
- `make unit` passes (4/4 unit tests)
- `make test` passes all tests (9/9 total)
- Full workflow reproducible via Makefile commands

---

**Challenges**
- Module import issue (`ModuleNotFoundError`)
- DB readiness timing (container not ready immediately)
- Confusion between pipeline smoke vs DB smoke
- Distinguishing unit tests vs integration tests

---

**Fixes**
- Used module execution (`python -m scripts.migrate`)
- Set `PYTHONPATH := src` in Makefile
- Added `wait_for_db()` to ensure DB readiness
- Separated test layers:
  - `unit` (no DB, fast)
  - `db-smoke` (DB connectivity)
  - full `test` (end-to-end)
- Added deterministic timeout test for robustness

---

**Outcome**
- Established a reproducible local data stack with Postgres
- Migration + seed + test workflow fully automated
- Added proper testing hierarchy (unit + integration + pipeline)
- Improved system robustness with failure-case testing
- Repository now demonstrates real-world Data Engineering practices:
  - reproducibility
  - layered testing
  - infrastructure + pipeline integration

---

### W02D3 (2026-02-25) — DB Smoke Test + CI Alignment--------------------

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

**Challenges**
- `PytestUnknownMarkWarning` for `smoke`
- Confusion with SQL parameter tuple `(table_name,)`
- Local vs CI DB startup difference
- CI failure due to `docker compose` dependency

**Fixes**
- Added marker config in `pytest.ini`
- Fixed SQL parameter format `(table_name,)`
- Removed `db-up` from `db-smoke` in CI
- Clarified execution model:
  - Local → manual DB setup
  - CI → service container

**Outcome**
- Established stable DB smoke testing workflow
- CI-compatible testing achieved
- Clear separation of concerns:
  - Infrastructure vs testing
- Ready for next steps:
  - W02D4 (data load into Postgres)
  - W02D5 (pipeline integration)

### W02D4 (2026-02-26) — CI Integration + End-to-End Reproducibility

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

**Challenges**
- `ModuleNotFoundError: de_lakehouse_pipeline` when running migrate
- PYTHONPATH inconsistencies between Windows, Makefile, and CI
- Conflict between local Docker workflow and CI Postgres service
- Ambiguity between pipeline smoke tests vs DB smoke tests

**Fixes**
- Introduced `pyproject.toml` and installed project with `pip install -e .`
- Removed reliance on fragile `PYTHONPATH`
- Split DB smoke targets: `db-smoke` (CI-safe) vs `db-smoke-local`
- Updated CI to rely only on Makefile commands
- Clarified README commands and DB workflow

**Outcome**
- Fully reproducible pipeline from clean environment
- Stable Postgres integration (local + CI)
- All tests passing (unit + pipeline + DB)
- Project upgraded to “production-style” reproducibility standard
- Repository is now runnable, testable, and CI-validated end-to-end



### W02D5 (2026-02-28) — Establish SQL Patterns, Data Quality Checks, and Initial SQL Tests

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

**Challenges**
- SQL examples were initially mixed inside migration files, which is not best practice.
- SQL tests originally executed only a single statement from the SQL file.
- Duplicate-check query produced multiple rows, which conflicted with test expectations.

**Fixes**
- Separated repository responsibilities:
  - `migrations/` for schema evolution only.
  - `sql/` for reusable query patterns and validation logic.
- Updated SQL tests to execute statements sequentially and safely.
- Modified duplicate detection query to return a summarized result compatible with tests.

**Outcome**
- Established the initial **SQL foundation layer** for the pipeline.
- Introduced reusable SQL patterns and automated validation queries.
- Integrated SQL checks into the testing workflow.
- Strengthened reproducibility through proof logs and documentation updates.
- Project now includes a structured SQL layer supporting future data quality and transformation logic.

# Week 02 Summary---------------------------------------------------------------------------------------

### System Capability
- Postgres-backed storage layer
- Versioned database migrations
- Seed workflow for deterministic test data
- Layered testing (unit + DB smoke + pipeline)
- Reproducible DB workflow via Makefile
- CI pipeline with Postgres service

### Engineering Guarantees
- Reproducibility: full stack runs from clean environment
- Determinism: migrations + seed ensure consistent DB state
- Testability: DB unit tests + integration smoke tests
- Automation: CI validates migrations and DB connectivity

### Metrics
- CI passing (GitHub Actions with Postgres service)
- Migration runtime: <10s
- Full pipeline runtime: <2 minutes
- Tests: unit + DB smoke + pipeline tests passing

### Gaps / Next Risks
- SQL modeling layer still minimal
- Data quality checks not yet enforced
- Observability/logging still missing
- No query performance optimization yet
- ERD and data model documentation still evolving


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
- Verified correct SQL statement splitting logic
- Recorded proof of successful test execution

**Validation**
- Ran lint check:
  - `make lint`
  - Result: All checks passed
- Ran unit tests:
  - `make sql-utils`
  - Result: 4 tests passed
- Proof log recorded under:
  - `docs/proof/2026-03-05-run.txt`


### W03D3 (2026-03-06) — Data Model Alignment & ERD

**Deliverables**
- Updated `docs/DATA_MODEL.md` to align with the current `users` table schema
- Added a simple ERD for the `users` table to visualize structure and relationships
- Ensured documentation reflects the latest schema fields (`id`, `name`, `created_at`, `updated_at`)
- Added proof record under `docs/proof/`

**Validation**
- Ran `make lint`
- Ran `make test`
- Verified documentation matches the current schema implementation
- Confirmed repository checks passed locally


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

### W03D5 (2026-03-08) — Extraction Layer Core Logic
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


## Week 04 — Extraction Layer

### W04D3 (2026-03-11) — Extraction Unit Tests

**Deliverables**
- Implemented unit tests for `save_raw_data`
- Implemented edge tests for `fetch_current_weather`
- Verified error handling when API key is missing

**Validation**
- Ran `make lint`
- Ran `pytest tests/test_extraction.py`
- All tests passed locally
