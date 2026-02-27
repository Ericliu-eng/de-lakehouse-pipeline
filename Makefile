#Tell make:These names are "targets", not files.
.PHONY: setup lint test run migrate db-up db-down smoke proof

VENV := .venv
PY_WIN := $(VENV)/Scripts/python.exe
PY_NIX := $(VENV)/bin/python


# Choose python path depending on OS (Windows_NT is set on Windows)
ifeq ($(OS),Windows_NT)
	PY := $(PY_WIN)
else
	PY := $(PY_NIX)
endif



setup:
	python -m venv $(VENV)
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -r requirements.txt
	$(PY) -m pip install -e .

lint:#.venv/Scripts/python.exe -m ruff check 
	$(PY) -m ruff check .



clean:
	rm -rf $(VENV)

test:   #-V verbose  -k .. 模糊
	$(PY) -m pytest -v	

unit:	#-k = Filter tests by "name keywords"
	$(PY) -m pytest -v tests/test_db_unit.py

run:
	$(PY) -m de_lakehouse_pipeline.main

smoke:	#在 Python 里：-m = run modul ,in pytest -m is marker

	$(PY) -m pytest -m smoke

# --- DB ---------------

db-up:  # -d 后台运行
	docker compose up -d

db-down:
	docker compose down
migrate:
	$(PY) -m scripts.migrate
	
#this for CI
db-smoke:
	$(PY) -m pytest -q tests/test_db_smoke.py -vv

db-smoke-local: db-up migrate db-smoke