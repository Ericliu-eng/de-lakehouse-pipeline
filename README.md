# de-lakehouse-pipeline

A lakehouse-style data engineering pipeline repo (skeleton) with reproducible commands and CI.

---

## What this project does

This project implements a simple data pipeline:

- Extract: reads raw CSV data
- Transform: removes invalid rows (missing name, non-positive amount)
- Load: writes cleaned data to processed folder

---

## Quickstart

```bash
cp .env.example .env
make setup
make lint
make test
python -m src.de_lakehouse_pipeline.main