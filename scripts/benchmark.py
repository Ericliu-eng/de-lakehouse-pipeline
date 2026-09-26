"""Measure pipeline correctness, reliability, and latency against saved payloads.

The benchmark replays Alpha Vantage payloads already saved under data/raw (and
Tiingo history payloads, when present, for the at-scale scenario), so it makes
no API calls. It creates a dedicated PostgreSQL database (default
``lakehouse_benchmark``), runs every migration there, and drops it afterwards;
the development database named by DB_NAME is never written to. Raw files and
backfill checkpoints go to a temporary directory.

Usage:
    python -m scripts.benchmark
    python -m scripts.benchmark --symbols AAPL MSFT --repeats 3 --output -
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import platform
import statistics
import subprocess
import tempfile
import time
from contextlib import contextmanager, redirect_stdout
from datetime import date, timedelta
from io import StringIO
from pathlib import Path
from unittest import mock

import psycopg
import requests
from psycopg import sql

from de_lakehouse_pipeline import backfill, pipeline, tiingo_backfill
from de_lakehouse_pipeline.cli import run_marts
from de_lakehouse_pipeline.ingest import io as raw_io
from de_lakehouse_pipeline.ingest import market_data_client
from de_lakehouse_pipeline.load.db.connection import connect, load_db_config, make_dsn, wait_for_db
from de_lakehouse_pipeline.quality.checks import run_stock_quality_checks
from orchestration.dagster_pipeline import run_orchestrated_pipeline
from scripts.migrate import list_migration_files, run_sql_file

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "alpha_vantage"
SERIES_KEY = "Time Series (Daily)"
FRESHNESS_MAX_AGE_DAYS = 14
BENCHMARK_TABLES = [
    "market_bars",
    "pipeline_metadata",
    "load_metadata",
    "mart_daily_symbol_summary",
    "mart_symbol_latest_price",
    "mart_symbol_volume_rank",
]


# --------------------------------------------------------------------------- #
# Inputs and database helpers
# --------------------------------------------------------------------------- #

def load_latest_payloads(raw_dir: Path, min_rows: int) -> tuple[dict[str, dict], list[str]]:
    """Return the most recent saved payload per symbol and the skipped symbols."""
    latest: dict[str, dict] = {}
    for path in raw_dir.glob("*/*/stock.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        series = payload.get(SERIES_KEY)
        if not series:
            continue
        symbol = payload["Meta Data"]["2. Symbol"].strip().upper()
        current = latest.get(symbol)
        if current is None or max(series) > max(current[SERIES_KEY]):
            latest[symbol] = payload

    skipped = sorted(s for s, p in latest.items() if len(p[SERIES_KEY]) < min_rows)
    kept = {s: p for s, p in sorted(latest.items()) if s not in skipped}
    return kept, skipped


def load_latest_tiingo_payloads(raw_dir: Path, symbols) -> dict[str, list[dict]]:
    """Return the most recent saved Tiingo history per symbol, keyed by symbol."""
    latest: dict[str, list[dict]] = {}
    for path in raw_dir.glob("*/*/tiingo.json"):
        symbol = path.parent.name.upper()
        if symbol not in symbols:
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(payload, list) or not payload:
            continue
        current = latest.get(symbol)
        if current is None or max(b["date"] for b in payload) > max(b["date"] for b in current):
            latest[symbol] = payload
    return dict(sorted(latest.items()))


def without_latest_days(payload: dict, days: int) -> dict:
    """Copy a payload with its newest ``days`` trading dates removed."""
    kept_dates = sorted(payload[SERIES_KEY])[:-days] if days else sorted(payload[SERIES_KEY])
    return {
        "Meta Data": payload["Meta Data"],
        SERIES_KEY: {d: payload[SERIES_KEY][d] for d in kept_dates},
    }


def recreate_database(name: str) -> None:
    cfg = load_db_config()
    if name == cfg.dbname:
        raise SystemExit(f"Refusing to use the configured database {name!r} for benchmarking.")
    wait_for_db(cfg, timeout_s=60)
    with psycopg.connect(make_dsn(cfg), autocommit=True) as conn:
        conn.execute(sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(name)))
        conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))


def drop_database(name: str) -> None:
    with psycopg.connect(make_dsn(load_db_config()), autocommit=True) as conn:
        conn.execute(sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(name)))


def migrate() -> None:
    with connect(load_db_config()) as conn:
        for path in list_migration_files(ROOT / "migrations"):
            run_sql_file(conn, path)


def scalar(query: str, params: tuple = ()):
    with connect(load_db_config()) as conn:
        return conn.execute(query, params).fetchone()[0]


def execute(query: str, params: tuple = ()) -> None:
    with connect(load_db_config()) as conn:
        conn.execute(query, params)


def reset_tables() -> None:
    execute("TRUNCATE " + ", ".join(BENCHMARK_TABLES))


def table_counts(tables: list[str]) -> dict[str, int]:
    return {t: scalar(f"SELECT COUNT(*) FROM {t}") for t in tables}


def duplicate_key_groups() -> int:
    return scalar(
        "SELECT COUNT(*) FROM (SELECT ts, symbol FROM market_bars "
        "GROUP BY ts, symbol HAVING COUNT(*) > 1) AS dup"
    )


def watermark(symbol: str):
    return scalar(
        "SELECT last_watermark::date FROM pipeline_metadata WHERE source = %s AND symbol = %s",
        (SOURCE, symbol),
    )


@contextmanager
def replay(payloads: dict[str, dict], raw_root: Path):
    """Serve saved payloads instead of calling the API and keep raw files out of data/raw."""
    calls = {"fetch": 0}

    def fake_fetch(symbol: str = "AAPL") -> dict:
        calls["fetch"] += 1
        return payloads[symbol.strip().upper()]

    def save_to_temp(data, name, root=None, run_date=None):
        return raw_io.save_raw_data(data, name, raw_root, run_date)

    with (
        mock.patch.object(pipeline, "fetch_daily_stock", fake_fetch),
        mock.patch.object(backfill, "fetch_daily_stock", fake_fetch),
        mock.patch.object(pipeline, "save_raw_data", save_to_temp),
        mock.patch.object(backfill, "CHECKPOINT_PATH", raw_root / "backfill_checkpoint.json"),
    ):
        yield calls


def timed(fn) -> tuple[object, float]:
    start = time.perf_counter()
    result = fn()
    return result, time.perf_counter() - start


# --------------------------------------------------------------------------- #
# Scenarios
# --------------------------------------------------------------------------- #

def bench_incremental(payloads: dict[str, dict], raw_root: Path, holdout: int) -> dict:
    reset_tables()
    staged = sum(len(p[SERIES_KEY]) for p in payloads.values())
    initial_payloads = {s: without_latest_days(p, holdout) for s, p in payloads.items()}

    with replay(initial_payloads, raw_root):
        _, initial_s = timed(lambda: [pipeline.run_stock(s) for s in payloads])
    initial_rows = scalar("SELECT COUNT(*) FROM market_bars")
    initial_audits = scalar("SELECT COUNT(*) FROM load_metadata")
    watermarks_before = {s: watermark(s) for s in payloads}

    with replay(payloads, raw_root):
        _, incremental_s = timed(lambda: [pipeline.run_stock(s) for s in payloads])
    incremental_rows = scalar("SELECT COUNT(*) FROM market_bars") - initial_rows
    watermarks_after = {s: watermark(s) for s in payloads}
    expected_watermarks = {s: date.fromisoformat(max(p[SERIES_KEY])) for s, p in payloads.items()}
    audits_after_incremental = scalar("SELECT COUNT(*) FROM load_metadata")

    with replay(payloads, raw_root):
        _, rerun_s = timed(lambda: [pipeline.run_stock(s) for s in payloads])
    total_rows = scalar("SELECT COUNT(*) FROM market_bars")

    return {
        "symbols": len(payloads),
        "staged_rows_per_run": staged,
        "initial_rows": initial_rows,
        "initial_seconds": initial_s,
        "initial_audits": initial_audits,
        "holdout_days": holdout,
        "incremental_rows": incremental_rows,
        "incremental_seconds": incremental_s,
        "watermarks_advanced": sum(
            watermarks_after[s] == expected_watermarks[s] and watermarks_after[s] > watermarks_before[s]
            for s in payloads
        ),
        "incremental_audits": audits_after_incremental - initial_audits,
        "rerun_rows": total_rows - initial_rows - incremental_rows,
        "rerun_seconds": rerun_s,
        "rerun_watermarks_unchanged": sum(watermark(s) == watermarks_after[s] for s in payloads),
        "rerun_audits": scalar("SELECT COUNT(*) FROM load_metadata") - audits_after_incremental,
        "total_rows": total_rows,
        "duplicate_key_groups": duplicate_key_groups(),
        "first_date": scalar("SELECT MIN(ts)::date FROM market_bars"),
        "last_date": scalar("SELECT MAX(ts)::date FROM market_bars"),
    }


def bench_quality_and_marts(payloads: dict[str, dict], raw_root: Path) -> dict:
    """Clean data passes the gate; injected bad rows stop the orchestrated run before marts."""
    reset_tables()
    with replay(payloads, raw_root):
        clean_runs = [run_orchestrated_pipeline(s) for s in payloads]

    with connect(load_db_config()) as conn:
        clean_checks = [r for s in payloads for r in run_stock_quality_checks(conn, symbol=s)]
    mart_rows = table_counts(BENCHMARK_TABLES[3:])

    symbol = next(iter(payloads))
    last_day = date.fromisoformat(max(payloads[symbol][SERIES_KEY]))
    bad_days = [last_day + timedelta(days=1), last_day + timedelta(days=2)]
    execute(
        "INSERT INTO market_bars (ts, symbol, open, high, low, close, volume, source) VALUES "
        "(%s, %s, 1, 1, 1, -1, 100, %s), (%s, %s, 1, 1, 1, 1, -100, %s)",
        (bad_days[0], symbol, SOURCE, bad_days[1], symbol, SOURCE),
    )
    with replay(payloads, raw_root):
        bad_run = run_orchestrated_pipeline(symbol)
    with connect(load_db_config()) as conn:
        bad_checks = run_stock_quality_checks(conn, symbol=symbol)
    bad_rows_in_marts = scalar(
        "SELECT COUNT(*) FROM mart_daily_symbol_summary WHERE symbol = %s AND trading_date >= %s",
        (symbol, bad_days[0]),
    )
    execute("DELETE FROM market_bars WHERE symbol = %s AND ts::date >= %s", (symbol, bad_days[0]))

    return {
        "clean_runs_succeeded": sum(r.status == "success" for r in clean_runs),
        "clean_runs": len(clean_runs),
        "checks_per_symbol": len(clean_checks) // len(payloads),
        "clean_checks_passed": sum(r.passed for r in clean_checks),
        "clean_checks": len(clean_checks),
        "mart_rows": mart_rows,
        "bad_rows_injected": len(bad_days),
        "bad_run_status": bad_run.status,
        "bad_run_steps": [(step.step_name, step.status) for step in bad_run.steps],
        "failed_checks": [(r.check_name, r.details) for r in bad_checks if not r.passed],
        "bad_rows_caught": sum(r.failed_rows for r in bad_checks if r.check_name == "range"),
        "bad_rows_in_marts": bad_rows_in_marts,
    }


def bench_atomic_rollback(payloads: dict[str, dict], raw_root: Path) -> dict:
    """Reject the audit insert after fact and watermark writes; nothing may persist."""
    reset_tables()
    symbol = next(iter(payloads))
    with replay({symbol: without_latest_days(payloads[symbol], 1)}, raw_root):
        pipeline.run_stock(symbol)
    tables = ["market_bars", "pipeline_metadata", "load_metadata"]
    before = table_counts(tables)
    watermark_before = watermark(symbol)

    execute("ALTER TABLE load_metadata ADD CONSTRAINT benchmark_reject_audit CHECK (record_count < 0) NOT VALID")
    error = None
    with replay(payloads, raw_root):
        try:
            pipeline.run_stock(symbol)
        except psycopg.errors.CheckViolation as exc:
            error = type(exc).__name__
    after_failure = table_counts(tables)
    watermark_after_failure = watermark(symbol)
    execute("ALTER TABLE load_metadata DROP CONSTRAINT benchmark_reject_audit")

    with replay(payloads, raw_root):
        pipeline.run_stock(symbol)
    after_retry = table_counts(tables)

    return {
        "symbol": symbol,
        "error": error,
        "before": before,
        "after_failure": after_failure,
        "watermark_unchanged": watermark_after_failure == watermark_before,
        "after_retry": after_retry,
        "watermark_after_retry": watermark(symbol),
    }


def bench_backfill_resume(payloads: dict[str, dict], raw_root: Path, window_days: int) -> dict:
    """Crash a backfill part-way, rerun it, and verify no gaps or duplicates remain."""
    reset_tables()
    symbol = next(iter(payloads))
    payload = payloads[symbol]
    end = date.fromisoformat(max(payload[SERIES_KEY]))
    start = end - timedelta(days=window_days - 1)
    trading_days = {d for d in payload[SERIES_KEY] if start.isoformat() <= d <= end.isoformat()}
    crash_after = len(trading_days) // 2

    real_run_for_date = backfill.run_stock_for_date
    processed: list[date] = []

    def crashing_run_for_date(target_date, **kwargs):
        if target_date.isoformat() in trading_days:
            if len(processed) == crash_after:
                raise RuntimeError("simulated crash")
            processed.append(target_date)
        return real_run_for_date(target_date, **kwargs)

    def loaded_days() -> set[str]:
        with connect(load_db_config()) as conn:
            rows = conn.execute(
                "SELECT DISTINCT ts::date FROM market_bars WHERE symbol = %s AND ts::date BETWEEN %s AND %s",
                (symbol, start, end),
            ).fetchall()
        return {r[0].isoformat() for r in rows}

    # run_backfill reports progress with print(); keep it out of the benchmark output.
    with replay(payloads, raw_root) as calls, redirect_stdout(StringIO()):
        with mock.patch.object(backfill, "run_stock_for_date", crashing_run_for_date):
            try:
                backfill.run_backfill(start, end, symbol=symbol)
            except RuntimeError:
                pass
        days_before_crash = len(loaded_days())
        calls_first_run = calls["fetch"]

        resumed: list[date] = []

        def counting_run_for_date(target_date, **kwargs):
            resumed.append(target_date)
            return real_run_for_date(target_date, **kwargs)

        with mock.patch.object(backfill, "run_stock_for_date", counting_run_for_date):
            _, resume_s = timed(lambda: backfill.run_backfill(start, end, symbol=symbol))
        calls_second_run = calls["fetch"] - calls_first_run

        with mock.patch.object(backfill, "run_stock_for_date", counting_run_for_date):
            resumed_before_noop = len(resumed)
            backfill.run_backfill(start, end, symbol=symbol)
        noop_processed = len(resumed) - resumed_before_noop

    final_days = loaded_days()
    resumed_trading = sum(d.isoformat() in trading_days for d in resumed[:resumed_before_noop])
    return {
        "symbol": symbol,
        "start": start,
        "end": end,
        "calendar_days": window_days,
        "trading_days": len(trading_days),
        "days_before_crash": days_before_crash,
        "resumed_calls": resumed_before_noop,
        "resumed_trading_days": resumed_trading,
        "resume_seconds": resume_s,
        "api_calls": [calls_first_run, calls_second_run],
        "gaps": len(trading_days - final_days),
        "duplicate_key_groups": duplicate_key_groups(),
        "noop_processed": noop_processed,
    }


class FakeResponse(requests.Response):
    def __init__(self, status_code: int, body: dict | None = None):
        super().__init__()
        self.status_code = status_code
        self._content = json.dumps(body or {}).encode()
        self.url = market_data_client.BASE_URL


def bench_retry() -> list[dict]:
    """Drive the real retry loop with scripted HTTP responses; backoff sleeps are recorded, not slept."""
    body = {"Meta Data": {}, SERIES_KEY: {}}
    cases = [
        ("429, 503, then 200", [FakeResponse(429), FakeResponse(503), FakeResponse(200, body)]),
        ("200 with throttle note, then 200",
         [FakeResponse(200, {"Note": "API call frequency exceeded"}), FakeResponse(200, body)]),
        ("Connection error, then 200", [requests.ConnectionError("reset"), FakeResponse(200, body)]),
        ("429 on every attempt", [FakeResponse(429)] * 5),
        ("400 bad request", [FakeResponse(400), FakeResponse(200, body)]),
    ]
    results = []
    for name, responses in cases:
        script = iter(responses)
        attempts = 0
        sleeps: list[float] = []

        def fake_get(*args, **kwargs):
            nonlocal attempts
            attempts += 1
            item = next(script)
            if isinstance(item, Exception):
                raise item
            return item

        with (
            mock.patch.object(market_data_client.requests, "get", fake_get),
            mock.patch.object(market_data_client.time, "sleep", sleeps.append),
        ):
            try:
                market_data_client.fetch_json_with_retry({"function": "TIME_SERIES_DAILY"})
                outcome = "success"
            except Exception as exc:
                outcome = f"raised {type(exc).__name__}"
        results.append({"case": name, "attempts": attempts, "outcome": outcome, "backoff": sleeps})
    return results


def bench_latency(payloads: dict[str, dict], raw_root: Path, repeats: int) -> dict:
    """Time the orchestrated ingest -> quality -> marts run from an empty warehouse."""
    batch_seconds: list[float] = []
    step_seconds: dict[str, list[float]] = {}
    run_seconds: list[float] = []
    statuses: list[str] = []
    for _ in range(repeats):
        reset_tables()
        with replay(payloads, raw_root):
            metrics, elapsed = timed(lambda: [run_orchestrated_pipeline(s) for s in payloads])
        batch_seconds.append(elapsed)
        for metric in metrics:
            data = metric.to_dict()
            statuses.append(metric.status)
            run_seconds.append(data["duration_seconds"])
            for step in data["steps"]:
                step_seconds.setdefault(step["step_name"], []).append(step["duration_seconds"])
    return {
        "repeats": repeats,
        "symbols": len(payloads),
        "succeeded": statuses.count("success"),
        "runs": len(statuses),
        "batch_seconds": batch_seconds,
        "run_seconds": run_seconds,
        "step_seconds": step_seconds,
    }


def bench_scale(payloads: dict[str, dict], tiingo_payloads: dict[str, list[dict]],
                raw_root: Path, repeats: int) -> dict:
    """Load daily rows, backfill full Tiingo history behind them, then time work over the result."""
    reset_tables()
    with replay(payloads, raw_root):
        for symbol in payloads:
            pipeline.run_stock(symbol)
    daily_rows = scalar("SELECT COUNT(*) FROM market_bars")

    def backfill_all():
        return [tiingo_backfill.run_tiingo_backfill(s, root=raw_root, payload=p)
                for s, p in tiingo_payloads.items()]

    backfills, load_s = timed(backfill_all)
    reruns, rerun_s = timed(backfill_all)

    def check_all():
        with connect(load_db_config()) as conn:
            return [r for s in payloads for r in run_stock_quality_checks(conn, symbol=s)]

    checks, quality_s = timed(check_all)
    _, marts_s = timed(run_marts)
    mart_rows = table_counts(BENCHMARK_TABLES[3:])

    # Daily orchestrated runs over the full warehouse; ingest finds no bars past
    # the watermark, so this measures the fixed cost of the gate and mart rebuild.
    batch_seconds: list[float] = []
    step_seconds: dict[str, list[float]] = {}
    statuses: list[str] = []
    for _ in range(repeats):
        with replay(payloads, raw_root):
            metrics, elapsed = timed(lambda: [run_orchestrated_pipeline(s) for s in payloads])
        batch_seconds.append(elapsed)
        for metric in metrics:
            statuses.append(metric.status)
            for step in metric.to_dict()["steps"]:
                step_seconds.setdefault(step["step_name"], []).append(step["duration_seconds"])

    recs = [b.reconciliation for b in backfills]
    diffs = [r.max_diff_pct for r in recs if r.max_diff_pct is not None]
    return {
        "symbols": len(tiingo_payloads),
        "daily_rows": daily_rows,
        "fetched_rows": sum(b.fetched_rows for b in backfills),
        "inserted_rows": sum(b.inserted_rows for b in backfills),
        "load_seconds": load_s,
        "rerun_inserted": sum(b.inserted_rows for b in reruns),
        "rerun_seconds": rerun_s,
        "total_rows": scalar("SELECT COUNT(*) FROM market_bars"),
        "first_date": scalar("SELECT MIN(ts)::date FROM market_bars"),
        "last_date": scalar("SELECT MAX(ts)::date FROM market_bars"),
        "duplicate_key_groups": duplicate_key_groups(),
        "overlap_days": sum(r.overlap_days for r in recs),
        "mismatched_days": sum(r.mismatched_days for r in recs),
        "max_diff_pct": max(diffs) if diffs else None,
        "tolerance_pct": recs[0].tolerance_pct,
        "checks_passed": sum(r.passed for r in checks),
        "checks": len(checks),
        "quality_seconds": quality_s,
        "marts_seconds": marts_s,
        "mart_rows": mart_rows,
        "repeats": repeats,
        "succeeded": statuses.count("success"),
        "runs": len(statuses),
        "batch_seconds": batch_seconds,
        "step_seconds": step_seconds,
    }


# --------------------------------------------------------------------------- #
# Report
# --------------------------------------------------------------------------- #

def environment() -> dict:
    def git(*args: str) -> str:
        try:
            return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True,
                                  check=True).stdout.strip()
        except (OSError, subprocess.CalledProcessError):
            return "unknown"

    commit = git("rev-parse", "--short", "HEAD")
    dirty = git("status", "--porcelain", "--untracked-files=no")
    return {
        "date": date.today().isoformat(),
        "commit": commit + (" (uncommitted changes)" if dirty else ""),
        "python": platform.python_version(),
        "postgres": scalar("SHOW server_version"),
        "os": f"{platform.system()} {platform.release()}",
    }


def ms(seconds: float) -> str:
    return f"{seconds * 1000:,.0f} ms"


def spread(values: list[float]) -> str:
    return (f"median {ms(statistics.median(values))} "
            f"(min {ms(min(values))}, max {ms(max(values))})")


def ok(flag: bool) -> str:
    return "pass" if flag else "**FAIL**"


def seconds(value: float) -> str:
    return f"{value:,.1f} s"


def render(env, inputs, inc, qm, atomic, bf, retry, lat, scale) -> str:
    symbols = ", ".join(inputs["symbols"])
    lines = [
        f"# Pipeline Benchmark — {env['date']}",
        "",
        "Generated by `python -m scripts.benchmark`. Saved Alpha Vantage payloads (and Tiingo "
        "history payloads for the at-scale section) were replayed into a dedicated PostgreSQL "
        "database, so no API calls were made and the development database was not modified. "
        "Timings are single-machine local measurements, not production SLAs.",
        "",
        "| Environment | Value |",
        "| --- | --- |",
        f"| Commit | `{env['commit']}` |",
        f"| Python / PostgreSQL | {env['python']} / {env['postgres']} |",
        f"| OS | {env['os']} |",
        f"| Input | {len(inputs['symbols'])} symbols ({symbols}); latest saved payload per symbol |",
    ]
    if inputs["skipped"]:
        lines.append(f"| Skipped (< {inputs['min_rows']} rows) | {', '.join(inputs['skipped'])} |")

    lines += ["", "## Headline results", ""]
    if scale:
        lines += [
            "### At scale (full price history, section 7)",
            "",
            "| Metric | Result |",
            "| --- | --- |",
            f"| Warehouse | {scale['total_rows']:,} rows · {scale['symbols']} symbols · "
            f"{scale['first_date']} to {scale['last_date']} |",
            f"| History backfill | {scale['inserted_rows']:,} rows inserted in {seconds(scale['load_seconds'])} "
            f"({scale['inserted_rows'] / scale['load_seconds']:,.0f} rows/s); rerun inserted "
            f"{scale['rerun_inserted']} |",
            f"| Cross-source reconciliation | {scale['overlap_days']:,} overlapping days; "
            f"{scale['mismatched_days']} closes differ by more than {scale['tolerance_pct']}% "
            f"(max {scale['max_diff_pct']}%) |",
            f"| Quality checks over full warehouse | {scale['checks_passed']}/{scale['checks']} passed "
            f"in {ms(scale['quality_seconds'])} |",
            f"| Mart rebuild over full warehouse | {seconds(scale['marts_seconds'])} |",
            f"| Daily {len(inputs['symbols'])}-symbol orchestrated run | "
            f"{spread(scale['batch_seconds'])} |",
            "",
        ]
    lines += [
        f"### Correctness and recovery ({inc['total_rows']:,}-row replay, sections 1–6)",
        "",
        "| Metric | Result |",
        "| --- | --- |",
        f"| Replay warehouse | {inc['total_rows']:,} rows · {inc['symbols']} symbols · "
        f"{inc['first_date']} to {inc['last_date']} |",
        f"| Rerun of identical payloads | {inc['rerun_rows']} new rows, "
        f"{inc['duplicate_key_groups']} duplicate keys |",
        f"| Incremental run | {inc['incremental_rows']} of {inc['staged_rows_per_run']:,} staged rows "
        f"loaded ({inc['holdout_days']} new days × {inc['symbols']} symbols) |",
        f"| Atomic rollback | {'no partial writes' if atomic['before'] == atomic['after_failure'] else '**partial writes**'} "
        f"in 3 tables after a rejected audit write |",
        f"| Backfill resume after crash | {bf['gaps']} missing trading days, "
        f"{bf['duplicate_key_groups']} duplicates |",
        f"| Quality gate | {qm['bad_rows_caught']} of {qm['bad_rows_injected']} injected bad rows caught; "
        f"{qm['bad_rows_in_marts']} reached marts |",
        f"| End-to-end run (ingest → quality → marts) | {spread(lat['run_seconds'])} per symbol |",
        f"| Full {lat['symbols']}-symbol batch | {spread(lat['batch_seconds'])} |",
        "",
        "## 1. Incremental loading and idempotency",
        "",
        f"Each symbol was first loaded without its newest {inc['holdout_days']} trading days, then "
        "with the full payload, then with the full payload again.",
        "",
        "| Run | Rows staged | Rows written | Audit rows | Time | Check |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
        f"| Initial | {inc['staged_rows_per_run'] - inc['holdout_days'] * inc['symbols']:,} | "
        f"{inc['initial_rows']:,} | {inc['initial_audits']} | {ms(inc['initial_seconds'])} | — |",
        f"| Incremental | {inc['staged_rows_per_run']:,} | {inc['incremental_rows']} | "
        f"{inc['incremental_audits']} | {ms(inc['incremental_seconds'])} | "
        f"watermark advanced for {inc['watermarks_advanced']}/{inc['symbols']} symbols: "
        f"{ok(inc['watermarks_advanced'] == inc['symbols'])} |",
        f"| Rerun | {inc['staged_rows_per_run']:,} | {inc['rerun_rows']} | {inc['rerun_audits']} | "
        f"{ms(inc['rerun_seconds'])} | watermark unchanged for "
        f"{inc['rerun_watermarks_unchanged']}/{inc['symbols']} symbols: "
        f"{ok(inc['rerun_rows'] == 0 and inc['rerun_watermarks_unchanged'] == inc['symbols'])} |",
        "",
        f"Duplicate `(ts, symbol)` groups after all runs: **{inc['duplicate_key_groups']}**.",
        "",
        "## 2. Transactional rollback",
        "",
        f"A CHECK constraint rejected the `load_metadata` insert for {atomic['symbol']}, after the "
        "fact upsert and watermark update had executed in the same transaction.",
        "",
        "| Table | Before | After failed run | After retry |",
        "| --- | ---: | ---: | ---: |",
    ]
    for table in atomic["before"]:
        lines.append(f"| `{table}` | {atomic['before'][table]} | {atomic['after_failure'][table]} | "
                     f"{atomic['after_retry'][table]} |")
    lines += [
        "",
        f"Error raised: `{atomic['error']}`. Watermark unchanged after failure: "
        f"{ok(atomic['watermark_unchanged'])}. Watermark after retry: {atomic['watermark_after_retry']}.",
        "",
        "## 3. Backfill crash and resume",
        "",
        f"Backfill of {bf['symbol']} for {bf['start']} to {bf['end']} ({bf['calendar_days']} calendar "
        f"days, {bf['trading_days']} trading days) was forced to fail after "
        f"{bf['days_before_crash']} trading days had loaded, then rerun.",
        "",
        "| Metric | Result |",
        "| --- | ---: |",
        f"| Trading days loaded before crash | {bf['days_before_crash']} |",
        f"| Dates processed on resume | {bf['resumed_calls']} ({bf['resumed_trading_days']} trading days; "
        "weekends are retried because they are never marked complete) |",
        f"| Resume time | {ms(bf['resume_seconds'])} |",
        f"| API payload fetches (first run, resume) | {bf['api_calls'][0]}, {bf['api_calls'][1]} |",
        f"| Missing trading days after resume | {bf['gaps']} |",
        f"| Duplicate keys | {bf['duplicate_key_groups']} |",
        f"| Trading dates reprocessed by a third, no-op run | {bf['noop_processed'] - (bf['calendar_days'] - bf['trading_days'])} |",
        "",
        "## 4. Quality gate",
        "",
        f"Clean data: {qm['clean_checks_passed']}/{qm['clean_checks']} checks passed "
        f"({qm['checks_per_symbol']} per symbol); {qm['clean_runs_succeeded']}/{qm['clean_runs']} "
        "orchestrated runs succeeded. Mart rows built: "
        + ", ".join(f"`{t}` {n:,}" for t, n in qm["mart_rows"].items()) + ".",
        "",
        f"Injected {qm['bad_rows_injected']} bad rows (one negative close, one negative volume). "
        f"The orchestrated run ended with status `{qm['bad_run_status']}`:",
        "",
        "| Step | Status |",
        "| --- | --- |",
    ]
    lines += [f"| {name} | {status} |" for name, status in qm["bad_run_steps"]]
    if len(qm["bad_run_steps"]) < 3:
        lines.append("| build_marts | not run |")
    lines += ["", "Failed checks:", ""]
    lines += [f"- `{name}`: {details}" for name, details in qm["failed_checks"]]
    lines += [
        "",
        f"Bad rows present in marts: **{qm['bad_rows_in_marts']}**.",
        "",
        "## 5. API retry behavior",
        "",
        "Scripted HTTP responses drove the real `fetch_json_with_retry` loop (max 3 retries). "
        "Backoff delays were recorded instead of slept.",
        "",
        "| Scenario | Attempts | Outcome | Backoff (s) |",
        "| --- | ---: | --- | --- |",
    ]
    lines += [f"| {r['case']} | {r['attempts']} | {r['outcome']} | "
              f"{', '.join(str(s) for s in r['backoff']) or '—'} |" for r in retry]
    lines += [
        "",
        "## 6. End-to-end latency",
        "",
        f"`run_orchestrated_pipeline` was run for each of {lat['symbols']} symbols from an empty "
        f"warehouse, {lat['repeats']} times ({lat['succeeded']}/{lat['runs']} runs succeeded).",
        "",
        "| Scope | Duration |",
        "| --- | --- |",
        f"| {lat['symbols']}-symbol batch | {spread(lat['batch_seconds'])} |",
        f"| One symbol, all steps | {spread(lat['run_seconds'])} |",
    ]
    lines += [f"| Step `{name}` | {spread(values)} |" for name, values in lat["step_seconds"].items()]
    lines += render_scale(scale, len(inputs["symbols"]))
    lines.append("")
    return "\n".join(lines)


def render_scale(scale, symbol_count: int) -> list[str]:
    lines = ["", "## 7. At scale: history backfill and daily runs", ""]
    if not scale:
        return lines + ["Skipped: no saved Tiingo payloads (`data/raw/*/*/tiingo.json`). "
                        "Run `make tiingo-backfill` first."]
    lines += [
        f"The Alpha Vantage payloads were loaded first ({scale['daily_rows']:,} rows), then the saved "
        f"Tiingo history for {scale['symbols']} symbols was backfilled behind them, as in production.",
        "",
        "| Metric | Result |",
        "| --- | ---: |",
        f"| Tiingo bars staged | {scale['fetched_rows']:,} |",
        f"| Rows inserted | {scale['inserted_rows']:,} |",
        f"| Existing rows kept (not overwritten) | {scale['fetched_rows'] - scale['inserted_rows']:,} |",
        f"| Backfill time | {seconds(scale['load_seconds'])} "
        f"({scale['inserted_rows'] / scale['load_seconds']:,.0f} rows/s) |",
        f"| Rerun: rows inserted / time | {scale['rerun_inserted']} / {seconds(scale['rerun_seconds'])} |",
        f"| Warehouse rows | {scale['total_rows']:,} ({scale['first_date']} to {scale['last_date']}) |",
        f"| Duplicate `(ts, symbol)` groups | {scale['duplicate_key_groups']} |",
        f"| Overlapping days reconciled | {scale['overlap_days']:,}; {scale['mismatched_days']} beyond "
        f"{scale['tolerance_pct']}% (max {scale['max_diff_pct']}%) |",
        f"| Quality checks | {scale['checks_passed']}/{scale['checks']} passed in {ms(scale['quality_seconds'])} |",
        f"| Mart rebuild | {seconds(scale['marts_seconds'])}: "
        + ", ".join(f"`{t}` {n:,}" for t, n in scale["mart_rows"].items()) + " |",
        "",
        f"Daily orchestrated runs over the full warehouse, {scale['repeats']} times "
        f"({scale['succeeded']}/{scale['runs']} runs succeeded). Ingest found no bars past the "
        "watermark, so this is the fixed cost of the quality gate and the mart rebuild, which "
        "the runner performs once per symbol.",
        "",
        "| Scope | Duration |",
        "| --- | --- |",
        f"| {symbol_count}-symbol batch | {spread(scale['batch_seconds'])} |",
    ]
    lines += [f"| Step `{name}` | {spread(values)} |" for name, values in scale["step_seconds"].items()]
    return lines


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--raw-dir", type=Path, default=ROOT / "data" / "raw")
    parser.add_argument("--symbols", nargs="*", help="Limit to these symbols (default: all saved)")
    parser.add_argument("--min-rows", type=int, default=20, help="Skip payloads with fewer rows")
    parser.add_argument("--holdout", type=int, default=5, help="Days withheld to test incremental loads")
    parser.add_argument("--backfill-days", type=int, default=14, help="Calendar days in the backfill window")
    parser.add_argument("--repeats", type=int, default=5, help="Latency repetitions")
    parser.add_argument("--scale-repeats", type=int, default=3,
                        help="Daily-run repetitions over the full-history warehouse")
    parser.add_argument("--db-name", default="lakehouse_benchmark")
    parser.add_argument("--keep-db", action="store_true", help="Keep the benchmark database afterwards")
    parser.add_argument("--output", default=None,
                        help="Markdown report path, or '-' for stdout only "
                             "(default: docs/proof/<today>-benchmark.md)")
    parser.add_argument("--verbose", action="store_true", help="Show pipeline logs")
    args = parser.parse_args()

    if not args.verbose:
        logging.disable(logging.ERROR)
    os.environ["ENABLE_S3_RAW_UPLOAD"] = "false"

    payloads, skipped = load_latest_payloads(args.raw_dir, args.min_rows)
    if args.symbols:
        wanted = {s.upper() for s in args.symbols}
        missing = wanted - payloads.keys()
        if missing:
            raise SystemExit(f"No saved payload for: {', '.join(sorted(missing))}")
        payloads = {s: p for s, p in payloads.items() if s in wanted}
    if not payloads:
        raise SystemExit(f"No saved payloads under {args.raw_dir}; run `make run SYMBOL=AAPL` first.")

    newest = max(date.fromisoformat(max(p[SERIES_KEY])) for p in payloads.values())
    if (date.today() - newest).days > FRESHNESS_MAX_AGE_DAYS:
        print(f"Warning: newest saved bar is {newest}; the {FRESHNESS_MAX_AGE_DAYS}-day freshness "
              "check will fail. Refresh payloads with `make run` for a clean run.")

    tiingo_payloads = load_latest_tiingo_payloads(args.raw_dir, payloads.keys())
    if not tiingo_payloads:
        print("No saved Tiingo payloads; skipping the at-scale scenario.")

    admin_db = load_db_config().dbname
    recreate_database(args.db_name)
    os.environ["DB_NAME"] = args.db_name
    try:
        migrate()
        with tempfile.TemporaryDirectory(prefix="lakehouse-bench-") as tmp:
            raw_root = Path(tmp)
            steps = [
                ("incremental loading", lambda: bench_incremental(payloads, raw_root, args.holdout)),
                ("quality gate and marts", lambda: bench_quality_and_marts(payloads, raw_root)),
                ("atomic rollback", lambda: bench_atomic_rollback(payloads, raw_root)),
                ("backfill resume", lambda: bench_backfill_resume(payloads, raw_root, args.backfill_days)),
                ("API retry", bench_retry),
                ("end-to-end latency", lambda: bench_latency(payloads, raw_root, args.repeats)),
                ("history backfill at scale", lambda: bench_scale(
                    payloads, tiingo_payloads, raw_root, args.scale_repeats) if tiingo_payloads else None),
            ]
            results = []
            for name, fn in steps:
                print(f"Running {name}...", flush=True)
                results.append(fn())
        env = environment()
    finally:
        os.environ["DB_NAME"] = admin_db
        if not args.keep_db:
            drop_database(args.db_name)

    inputs = {"symbols": list(payloads), "skipped": skipped, "min_rows": args.min_rows}
    report = render(env, inputs, *results)
    if args.output == "-":
        print(report)
        return
    output = Path(args.output) if args.output else ROOT / "docs" / "proof" / f"{env['date']}-benchmark.md"
    output.write_text(report, encoding="utf-8")
    print(f"Report written to {output}")


if __name__ == "__main__":
    main()
