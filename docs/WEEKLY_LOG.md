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

### W02D2 (2026-02-24) — Postgres Core Logic + DB Smoke Test----------------------

**Deliverables**
- Completed Postgres-backed data workflow:
  - Docker Compose service (`db-up`, `db-down`)
  - Migration script (`scripts/migrate.py`) runs via module
  - Schema initialization (`init_db.sql`)
  - Seed data loading (`seed.sql`)
- Added DB smoke test:
  - `tests/test_db_smoke.py` verifies connectivity and query
- Refactored Makefile:
  - Added `db-up`, `db-down`, `migrate`, `db-smoke`
  - Standardized module execution (`-m`)
- Improved README:
  - Added Local Postgres workflow section
  - Documented reproducible commands
- Added proof artifact:
  - `docs/proof/2026-02-24_w02d2_full_run.txt`

**Validation**
- `make db-up` successfully starts Postgres container
- `make migrate` applies schema and seed without errors
- `make db-smoke` passes (DB reachable + query works)
- `make test` passes all tests (5/5)
- End-to-end workflow reproducible from Makefile commands

**Challenges**
- Module import issue (`ModuleNotFoundError`)
- DB readiness timing (container not ready immediately)
- Confusion between pipeline smoke vs DB smoke

**Fixes**
- Used module execution (`python -m scripts.migrate`)
- Set `PYTHONPATH := src` in Makefile
- Added `wait_for_db()` to ensure DB readiness
- Separated `smoke` (pipeline) vs `db-smoke` (database)

**Outcome**
- Established a reproducible local data stack with Postgres
- Migration + seed + test workflow fully automated
- Clear separation of pipeline vs infrastructure validation
- Repository now demonstrates real DE workflow patterns