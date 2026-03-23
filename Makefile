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

test:   #-V verbose  -k **包含这个名字的
	$(PY) -m pytest tests -v

test-s:   #-V verbose  -k .. 模糊  输出 print
	$(PY) -m pytest tests -s

run:
	$(PY) -m de_lakehouse_pipeline.cli run_stock

smoke:	#在 Python 里：-m = run modul ,in pytest -m is marker
	$(PY) -m pytest -m smoke


# --- DB ---------------
#this for CI

db-shell:
	docker exec -it de_lakehouse_db psql -U lakehouse -d lakehouse

db-up:  # -d 后台运行
	docker compose up -d

db-down:
	docker compose down
db-migrate:
	$(PY) -m scripts.migrate
db-seed:
	$(PY) -m scripts.seed_db
	
db-smoke-local: db-up migrate db-smoke
db-visu:
	$(PY) -m de_lakehouse_pipeline.checkdb view_market_bars