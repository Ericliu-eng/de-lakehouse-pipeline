# de-lakehouse-pipeline

[![CI](https://github.com/Ericliu-eng/de-lakehouse-pipeline/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Ericliu-eng/de-lakehouse-pipeline/actions/workflows/ci.yml)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776ab)
![PostgreSQL 16](https://img.shields.io/badge/PostgreSQL-16-336791)
![Dagster](https://img.shields.io/badge/Dagster-4f43dd)
![FastAPI](https://img.shields.io/badge/FastAPI-009688)

A market-data pipeline that loads daily prices from Alpha Vantage and decades of history from Tiingo into an incremental PostgreSQL warehouse. Analytical marts rebuild only after a quality gate passes, and a FastAPI dashboard serves the results.

![Animated flow: a daily AAPL load is throttled and retried, lands as raw JSON, is validated and typed, filtered by the watermark to one new bar, and committed with its watermark and audit row in one transaction; the quality gate passes, the three marts rebuild, FastAPI serves the latest price, and the run is reported to PipeGuard; a Tiingo history backfill then inserts missing bars without overwriting existing ones, and saved benchmark results light up](docs/demo/pipeline-flow.gif)

<sub>Illustrated flow, not a recording. Prices are examples. Rendered by [`docs/demo/render_flow.py`](docs/demo/render_flow.py) · [static frame](docs/demo/pipeline-flow.png)</sub>

## Results

| What | Result | Conditions |
| --- | --- | --- |
| History backfill | **97,276 rows in 7.2 s**; rerun inserts 0; **0 of 1,219** overlapping closes off by > 0.5% | 10 symbols, 1970–2026, PostgreSQL 16 · [details](docs/BENCHMARKS.md#full-price-history) |
| Reruns and failures | **0 duplicate keys** on rerun; **no partial writes** after a rejected audit insert | Real PostgreSQL rollback across three tables · [details](docs/BENCHMARKS.md#correctness-and-recovery-1000-row-alpha-vantage-replay) |
| Quality gate | **2 / 2 injected bad rows caught**, marts not rebuilt; 60 / 60 checks on 98k rows in 0.4 s | [details](docs/BENCHMARKS.md#correctness-and-recovery-1000-row-alpha-vantage-replay) |
| Tests | **220 tests, 88% line coverage** | Fresh migrated database · [details](docs/BENCHMARKS.md#tests-and-coverage) |

## How it works

- **Retries:** HTTP 429/5xx, timeouts, and throttle messages back off 1, 2, then 4 s; API keys are masked in every error.
- **Raw first, then typed:** each payload is saved as JSON (optional S3 copy) before staging validates and casts every field.
- **Incremental and atomic:** a watermark per `(source, symbol)` keeps only newer bars; fact rows, watermark, and load audit commit or roll back together.
- **Quality gate:** not-null and unique keys, non-negative values, and 14-day freshness. A failure stops the run before the marts rebuild.
- **Insert-only history:** Tiingo fills only missing `(ts, symbol)` keys, never overwriting daily rows, and compares overlapping closes.
- **Run monitoring:** each CLI run is recorded in `pipeline_runs` and reported to [PipeGuard](https://github.com/Ericliu-eng/pipeguard) for cross-run anomaly checks; reporting never fails a load.

More in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md): components, the data model, and design decisions.

## Quick start

Needs Python 3.10+, GNU Make, and Docker with Compose (port `5432` free).

```bash
git clone https://github.com/Ericliu-eng/de-lakehouse-pipeline.git
cd de-lakehouse-pipeline
make setup
cp .env.example .env
make db-up
make db-migrate
make db-seed
```

Set `ALPHA_VANTAGE_API_KEY` in `.env` (and `TIINGO_API_TOKEN` for history), then run one symbol end to end and start the API:

```bash
make orchestrate SYMBOL=AAPL
make tiingo-backfill SYMBOL=AAPL
make run-marts
source .venv/bin/activate
python -m src.serve.api
```

Open **http://127.0.0.1:8000/dashboard**. `make dagster-dev` starts the Dagster UI with the same ingest → checks → marts job and a daily schedule.

<details>
<summary>Windows PowerShell</summary>

Use `Copy-Item .env.example .env` instead of `cp`, and activate the environment with `.\.venv\Scripts\Activate.ps1` instead of `source .venv/bin/activate`. Use `curl.exe` rather than `curl` to query the API.
</details>

## Tests

```bash
make lint
make unit
make smoke
```

These need no database. `make test` adds the PostgreSQL smoke and integration suites; run it against a disposable database, because those tests delete rows. CI runs lint, every suite on PostgreSQL 16, and `terraform test`.

## Documentation

| Topic | Document |
| --- | --- |
| Architecture and data model | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), [docs/DATA_MODEL.md](docs/DATA_MODEL.md), [docs/DEMO_QUERIES.md](docs/DEMO_QUERIES.md) |
| Benchmarks, tests, and coverage | [docs/BENCHMARKS.md](docs/BENCHMARKS.md) |
| Setup and operations | [docs/DEV_SETUP.md](docs/DEV_SETUP.md), [docs/RUNBOOK.md](docs/RUNBOOK.md) |
| Incremental loading and backfill | [docs/INCREMENTAL.md](docs/INCREMENTAL.md), [docs/BACKFILL.md](docs/BACKFILL.md) |
| Data quality and failure drills | [docs/DATA_QUALITY.md](docs/DATA_QUALITY.md), [docs/FAILURE_DRILLS.md](docs/FAILURE_DRILLS.md) |
| Orchestration and run monitoring | [docs/ORCHESTRATION.md](docs/ORCHESTRATION.md), [docs/OPS_METRICS.md](docs/OPS_METRICS.md) |
| S3 storage and Terraform | [docs/CLOUD_STORAGE.md](docs/CLOUD_STORAGE.md), [infra/terraform/README.md](infra/terraform/README.md) |
| Limitations and next steps | [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md#open-items) |
