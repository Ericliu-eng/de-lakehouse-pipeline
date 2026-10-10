# de-lakehouse-pipeline

[![CI](https://github.com/Ericliu-eng/de-lakehouse-pipeline/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Ericliu-eng/de-lakehouse-pipeline/actions/workflows/ci.yml)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776ab)
![PostgreSQL 16](https://img.shields.io/badge/PostgreSQL-16-336791)
![Dagster](https://img.shields.io/badge/Dagster-4f43dd)
![FastAPI](https://img.shields.io/badge/FastAPI-009688)

A market-data pipeline that loads daily prices from Alpha Vantage and decades of history from Tiingo into an incremental PostgreSQL warehouse. The manual CLI and orchestrated workflows build analytical marts after a quality gate passes. A Streamlit dashboard explores price trends and daily changes, while a FastAPI service exposes the latest price from the analytical mart. Execution is validated locally with serial runs.

![Animated flow: a daily AAPL load is throttled and retried, lands as raw JSON, is validated and typed, filtered by the watermark to one new bar, and committed with its watermark and audit row in one transaction; the quality gate passes, the three marts rebuild, FastAPI serves the latest price, and the run is reported to PipeGuard; a Tiingo history backfill then inserts missing bars without overwriting existing ones, and saved benchmark results light up](docs/demo/lakehouse-flow.gif)

<sub>Illustrated flow, not a recording. Prices are examples. The illustration shows the earlier six-check gate; the current daily gate has seven checks. Rendered by [`docs/demo/render_flow.py`](docs/demo/render_flow.py) · [static frame](docs/demo/lakehouse-flow.png)</sub>

## Results

| What | Result | Conditions |
| --- | --- | --- |
| History backfill | **97,302 rows in 6.2 s**; rerun inserts 0; **0 of 974** overlapping closes off by > 0.5% | Saved-data replay, 10 symbols, 1970–2026, PostgreSQL 16, 2026-10-06 · [proof](docs/proof/2026-10-06-benchmark.md) |
| Reruns and failures | **0 duplicate keys** on rerun; **no partial writes** after a rejected audit insert | Real PostgreSQL rollback across three tables · [details](docs/BENCHMARKS.md#correctness-and-recovery-1000-row-alpha-vantage-replay) |
| Quality gate | **2 / 2 injected bad rows caught**, marts not rebuilt; 70 / 70 checks on 98k rows in 0.9 s | Local saved-data replay · [proof](docs/proof/2026-10-06-benchmark.md) |
| Tests | **281 tests, 88% line coverage** | Python 3.13, disposable PostgreSQL 16 · [proof](docs/proof/2026-10-06-resume-readiness.md) |

## How it works

- **Retries:** HTTP 429/500/502/503/504, timeouts, and throttle messages back off 1, 2, then 4 s; the retry helper masks API keys in HTTP and connection errors.
- **Raw first, then typed:** each payload is saved as JSON (optional S3 copy) before staging validates and casts every field.
- **Incremental and atomic:** a watermark per `(source, symbol)` keeps only newer bars; fact rows, watermark, and load audit commit or roll back together.
- **Quality gate:** not-null and unique keys, finite non-negative OHLCV, consistent price ranges, and no future trading dates. Daily orchestration also requires 0–14 day freshness; manual mart builds permit valid historical data.
- **Insert-only history:** Tiingo fills only missing `(ts, symbol)` keys, never overwriting daily rows, and compares overlapping closes.
- **Run monitoring:** each CLI-orchestrated run is recorded in `pipeline_runs` and, when configured, reported to [PipeGuard](https://github.com/Ericliu-eng/pipeguard) for cross-run anomaly checks; reporting never fails a load.

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

Set `ALPHA_VANTAGE_API_KEY` in `.env` (and `TIINGO_API_TOKEN` for history), then run one symbol end to end and open the stock price dashboard:

```bash
make orchestrate SYMBOL=AAPL
make tiingo-backfill SYMBOL=AAPL
make run-marts
make price-dashboard
```

Open [http://localhost:8501](http://localhost:8501), or the local URL printed by Streamlit. Select a symbol and row count to view its latest close, daily price change, price trend, and history table. This dashboard reads `market_bars`; PostgreSQL must be running (`make db-up` above) before launching it. Press Ctrl+C to stop the dashboard.

`make dagster-dev` starts the Dagster UI with the same ingest → checks → marts job and a daily schedule.

<details>
<summary>Windows PowerShell</summary>

Use `Copy-Item .env.example .env` instead of `cp`, and activate the environment with `.\.venv\Scripts\Activate.ps1` instead of `source .venv/bin/activate`. Use `curl.exe` rather than `curl` to query the API.
</details>

## Serving API

After the quick-start pipeline and mart build, start the FastAPI service:

```bash
make dashboard
```

This command starts PostgreSQL if needed and serves a minimal [latest-price page](http://127.0.0.1:8000/dashboard). It reads one latest record from `mart_symbol_latest_price` to demonstrate serving curated pipeline outputs. Use [GET /latest-price](http://127.0.0.1:8000/latest-price) for the JSON response and [GET /health](http://127.0.0.1:8000/health) for the service health check. Press Ctrl+C to stop the service.

## Tests

```bash
make lint
make unit
make smoke
```

These need no database. `make test-all` runs every test, including PostgreSQL smoke and integration suites; use a disposable database, because those tests delete rows. CI is configured for Python 3.10 and 3.13 with PostgreSQL 16, Ruff, and `terraform test`. Local verification for these fixes used Python 3.13; the updated CI matrix has not yet run.

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
