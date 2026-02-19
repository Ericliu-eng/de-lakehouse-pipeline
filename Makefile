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

setup:
	python -m venv $(VENV)
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -r requirements.txt

lint:
	$(PY) -m ruff check .

test:
	$(PY) -m pytest -v

clean:
	rm -rf $(VENV)
