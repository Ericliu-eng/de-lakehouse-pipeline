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


## Week 01 Summary------------------------------------------------------

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

### Next Focus
- Introduce Postgres-backed storage
- Add migration + schema management
- Add DB integration tests

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
- Added reproducible proof under `docs/proof/w02/2026-02-27-run`
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


