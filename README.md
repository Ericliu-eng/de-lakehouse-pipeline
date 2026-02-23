# de-lakehouse-pipeline

A lakehouse-style data engineering pipeline repo (skeleton) with reproducible commands and CI.

---

## What this project does

- Extract: read raw CSV  
- Transform: clean invalid rows  
- Load: write processed data  

---

## Quickstart
cp .env.example .env
make setup
make test
make run

---

## Local Postgres (Week 02)
make db-up
make migrate
make test

---

## Project Structure

src/de_lakehouse_pipeline/
scripts/
tests/
data/
docs/


---

## Notes

- Reproducible via Makefile  
- Tested locally + CI  
- Built for extension (DE → MLOps)  