# Development Setup

## Prerequisites

- Python 3.10+
- Git
- GNU Make
- Docker and Docker Compose

## Configure Environment

Create the local environment file.

PowerShell:

```powershell
Copy-Item .env.example .env
```

Bash:

```bash
cp .env.example .env
```

Update `.env` if your local PostgreSQL settings differ from the defaults.

## Install and Validate

Create the virtual environment, install dependencies, and run checks that do
not require PostgreSQL:

```bash
make setup
make lint
make unit
make smoke
```

Ruff is pinned to `0.15.8` in `requirements.txt`. The explicit project rules in
`pyproject.toml` are `E4`, `E7`, `E9`, and `F`, matching the baseline used for
local validation. Import sorting and additional strict rule groups are not
enabled by this baseline. Upgrade the pinned version and required version
together, and review rule changes before enabling them in CI.

## Full Database Validation

Start PostgreSQL, apply migrations, and run the default test suite:

```bash
make db-up
make db-migrate
make db-seed
make test
```

Live ingestion also requires `ALPHA_VANTAGE_API_KEY`.

## Shutdown

```bash
make db-down
```
