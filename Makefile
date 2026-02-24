.PHONY: setup lint test clean

VENV := .venv
PY_WIN := $(VENV)/Scripts/python.exe
PY_NIX := $(VENV)/bin/python

# Choose python path depending on OS (Windows_NT is set on Windows)
ifeq ($(OS),Windows_NT)
	PY := $(PY_WIN)
else
	PY := $(PY_NIX)
endif

export PYTHONPATH := src

setup:
	python -m venv $(VENV)
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -r requirements.txt

lint:
#.venv/Scripts/python.exe -m ruff check 
	$(PY) -m ruff check .


clean:
	rm -rf $(VENV)
	
test:
	$(PY) -m pytest -v -s
	

run:
	$(PY) -m de_lakehouse_pipeline.main

smoke:
	$(PY) -m pytest -v tests/test_smoke.py


db-up:  # -d 后台运行
	docker compose up -d

db-down:
	docker compose down

migrate:
	$(PY) -m scripts.migrate	