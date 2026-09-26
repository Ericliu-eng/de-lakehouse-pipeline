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

Activate the virtual environment in each new terminal after `make setup`:

```powershell
.\.venv\Scripts\Activate.ps1
```

```bash
source .venv/bin/activate
```

If PowerShell blocks activation, replace `python` with
`.\.venv\Scripts\python.exe`. Make targets already select the virtual
environment.

## Database Connection

The defaults match the PostgreSQL service in `docker-compose.yml`:
`localhost:5432`, with database, user, and password all set to `lakehouse`.

The ingestion module loads `.env`. Standalone migration, seed, and serving
commands read `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, and `DB_PASSWORD`
from the process environment. If you change the connection, export these
variables in the shell that runs those commands; editing `.env` alone is not
sufficient for those entry points.

Keep credentials in your local environment or the ignored `.env` file. Exclude
them from source code, command URLs, logs, and proof screenshots.

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

Fixtures delete selected test-date rows and rebuild marts, so use a disposable
development database. The seed inserts a small `TEST` fixture; it does not
populate the serving marts.

Live ingestion also requires `ALPHA_VANTAGE_API_KEY` in `.env`.

## Troubleshooting

- **`make setup` fails with `OSError: [Errno 2] No such file or directory` on
  Windows**, mentioning a long path under `site-packages\dagster`: Dagster
  installs deeply nested files that exceed Windows' default 260-character path
  limit when the repository is cloned in a deep directory. Clone to a short
  path such as `C:\src\de-lakehouse-pipeline`, or enable Windows long-path
  support.

## Shutdown

```bash
make db-down
```
