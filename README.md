# de-lakehouse-pipeline
A lakehouse-style data engineering pipeline skeleton with reproducible Make commands and CI.
---
## What this project does
- Extract: read raw CSV  
- Transform: clean invalid rows  
- Load: write processed data  
---


## Quickstart

```bash
cp .env.example .env
make setup
make lint
make test
make run
```
---

## Local Postgres (Week 02)

```bash
make db-up
make migrate
make smoke  # quick DB connectivity check
# or run full test suite
make test
```
## Reset (if needed)

```bash
make db-down
make db-up
make migrate
```
---

## Project Structure
src/de_lakehouse_pipeline/
scripts/
tests/
data/
docs/

## CI
GitHub Actions runs `make lint` and `make test` on each PR.
---
## Notes
- Reproducible via Makefile  
- Tested locally + CI  
- Built for extension (DE → MLOps)  