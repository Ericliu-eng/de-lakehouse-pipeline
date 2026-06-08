# Tell make: these names are targets, not files.
.PHONY: help setup lint clean unit smoke smoke-db integration test test-all test-s run run-marts backfill orchestrate cloud-storage-test tree db-up db-down db-migrate migrate db-seed db-smoke db-smoke-local db-shell db-visu sql-utils proof

.DEFAULT_GOAL := help

VENV := .venv
PY_WIN := $(VENV)/Scripts/python.exe
PY_NIX := $(VENV)/bin/python
SYMBOL ?= AAPL

ifeq ($(OS),Windows_NT)
	PY := $(PY_WIN)
else
	PY := $(PY_NIX)
endif

help:
	@echo "Available targets:"
	@echo "  unit          Run unit tests"
	@echo "  smoke         Run lightweight smoke tests without DB"
	@echo "  smoke-db      Run DB-backed smoke tests"
	@echo "  integration   Run DB-backed integration tests"
	@echo "  test          Run default local validation"
	@echo "  test-all      Run the full test suite"
	@echo "  db-up         Start Postgres"
	@echo "  migrate       Apply DB migrations"
	@echo "  db-seed       Seed DB"
	@echo "  run           Run stock pipeline"
	@echo "  run-marts     Build analytical marts"
	@echo "  backfill      Run date-range backfill with START, END, and optional SYMBOL"
	@echo "  cloud-storage-test Run AWS S3 raw storage unit tests"

setup:
	python -m venv $(VENV)
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -r requirements.txt
	$(PY) -m pip install -e .

lint:
	$(PY) -m ruff check .

clean:
	rm -rf $(VENV)

unit:
	$(PY) -m pytest tests/unit -v

smoke:
	$(PY) -m pytest tests/smoke -v

smoke-db:
	$(PY) -m pytest tests/smoke -m "smoke and db" -v

integration:
	$(PY) -m pytest tests/integration -v

test: unit smoke integration

test-all:
	$(PY) -m pytest tests -v

test-s:
	$(PY) -m pytest tests -s

sql-utils:
	$(PY) -m pytest tests/unit/test_sql_utils.py -v

run:
	$(PY) -m de_lakehouse_pipeline.cli run_stock 
	
run-o:
	$(PY) -m de_lakehouse_pipeline.cli run_stock --symbol MSFT
run-marts:
	$(PY) -m de_lakehouse_pipeline.cli run_marts

backfill:
	$(PY) -m de_lakehouse_pipeline.cli backfill --start $(START) --end $(END) --symbol $(SYMBOL)

orchestrate:
	$(PY) -m orchestration.dagster_pipeline --symbol $(SYMBOL)

cloud-storage-test:
	$(PY) -m pytest tests/unit/test_cloud_storage.py -v

tree:
	$(PY) tree_tool.py
	
terraform-check:
	cd infra/terraform && terraform fmt -check && terraform plan -var="raw_bucket_name=eric-lakehouse-raw-dev-20260601"

price-dashboard:
	$(PY) -m streamlit run scripts/price_dashboard.py

terraform-validate:
	cd infra/terraform && terraform fmt -check && terraform init -backend=false && terraform validate
	
#database ---

db-shell:
	docker exec -it de_lakehouse_db psql -U lakehouse -d lakehouse

db-up:
	docker compose up -d

db-down:
	docker compose down

db-migrate:
	$(PY) -m scripts.migrate

migrate: db-migrate

db-seed:
	$(PY) -m scripts.seed_db

db-smoke:
	$(PY) -m pytest tests/smoke/test_db_smoke.py -v

db-smoke-local: db-up migrate db-smoke

db-visu:
	$(PY) -m de_lakehouse_pipeline.checkdb view_market_bars

#-v =verbose
