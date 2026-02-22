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
**Next**
- Implement minimal ETL pipeline

-------

### Iteration 2 (2026-02-21) — MVP ETL Pipeline
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

---------

### Iteration 3 (2026-02-21) — Unit Testing
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

---------

### Iteration 4 (2026-02-21) — Smoke Test & CLI
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

---------

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
**Next**
- Demo rehearsal + documentation polish

---------

### Iteration 6 (2026-02-22) — Demo Rehearsal
**Deliverables**
- Verified full pipeline using README instructions
- Ensured project is runnable by external users
**Validation**
- End-to-end pipeline runs in <2 minutes
- No missing steps or hidden dependencies
**Outcome**
- Project is now reproducible, testable, and demo-ready

---------

## Week 01 Summary (2026-02-19 ~ 2026-02-22)
### What I built
- End-to-end data pipeline (Extract → Transform → Load)
- Reproducible repo structure with Makefile + CI
- Unit tests + smoke test for validation
- Documentation for setup and usage
### Metrics / Evidence
- All tests passing locally and in CI
- Pipeline processes sample data correctly
- Output file generated: data/processed/output.csv
- One-command execution via Makefile (run / smoke)
### Issues / Challenges
- Import issues with src/ structure
- Differences between local (Windows) and CI (Linux)
- Understanding pytest (tmp_path, structure)
### What I learned
- How to structure a real data engineering project
- Importance of reproducibility (Makefile + CI)
- Difference between unit testing and E2E testing
- CI can catch issues not seen locally
### Risks / Gaps
- Pipeline uses only sample data (not real dataset)
- No logging system (only print statements)
- No config management (.env or YAML not fully used)
