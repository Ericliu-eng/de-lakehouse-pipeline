"""Tiingo history backfill against real PostgreSQL in an isolated schema."""
from datetime import date
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest
from psycopg import sql

from de_lakehouse_pipeline import pipeline, tiingo_backfill
from de_lakehouse_pipeline.load.db.connection import connect, load_db_config

pytestmark = [pytest.mark.integration, pytest.mark.db]

SYMBOL = "BACKFILL"
ALPHA_VANTAGE_PAYLOAD = {
    "Meta Data": {"2. Symbol": SYMBOL, "5. Time Zone": "US/Eastern"},
    "Time Series (Daily)": {
        day: {"1. open": "1", "2. high": "1", "3. low": "1", "4. close": close, "5. volume": "10"}
        for day, close in [("2026-09-16", "100"), ("2026-09-17", "101"), ("2026-09-18", "102")]
    },
}
# Two older days, then three days that Alpha Vantage already loaded; 09-17 disagrees.
TIINGO_PAYLOAD = [
    {"date": f"{day}T00:00:00.000Z", "open": 1, "high": 1, "low": 1, "close": close, "volume": 20}
    for day, close in [
        ("2026-09-14", 98.0),
        ("2026-09-15", 99.0),
        ("2026-09-16", 100.0),
        ("2026-09-17", 105.0),
        ("2026-09-18", 102.0),
    ]
]


@pytest.fixture
def db(monkeypatch, tmp_path):
    cfg = load_db_config()
    schema = "test_tiingo_" + uuid4().hex
    with connect(cfg) as conn:
        conn.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))

    def open_connection(_cfg=None):
        conn = connect(cfg)
        conn.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(schema)))
        conn.commit()
        return conn

    try:
        with open_connection() as conn:
            root = Path(__file__).resolve().parents[2]
            for name in ["003_market_bars.sql", "004_load_metadata.sql",
                         "006_pipeline_metadata.sql", "008_add_source_to_market_bars.sql"]:
                conn.execute((root / "migrations" / name).read_text(encoding="utf-8"))
        for module in (pipeline, tiingo_backfill):
            monkeypatch.setattr(module, "connect", open_connection)
            monkeypatch.setattr(module, "wait_for_db", lambda *args, **kwargs: None)
        monkeypatch.setattr(pipeline, "fetch_daily_stock", lambda symbol: ALPHA_VANTAGE_PAYLOAD)
        monkeypatch.setenv("ENABLE_S3_RAW_UPLOAD", "false")
        pipeline.run_stock(SYMBOL, root=tmp_path)
        yield open_connection
    finally:
        with connect(cfg) as conn:
            conn.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


def bars(open_connection):
    with open_connection() as conn:
        rows = conn.execute("SELECT ts::date, close, source FROM market_bars ORDER BY ts").fetchall()
    return [(day.isoformat(), float(close), source) for day, close, source in rows]


def watermarks(open_connection):
    with open_connection() as conn:
        rows = conn.execute("SELECT source, last_watermark::date FROM pipeline_metadata").fetchall()
    return dict(rows)


def test_backfill_adds_history_without_overwriting_daily_rows(db, tmp_path):
    result = tiingo_backfill.run_tiingo_backfill(SYMBOL, root=tmp_path, payload=TIINGO_PAYLOAD)

    assert (result.fetched_rows, result.inserted_rows, result.skipped_rows) == (5, 2, 3)
    assert (result.first_date, result.last_date) == (date(2026, 9, 14), date(2026, 9, 18))
    assert bars(db) == [
        ("2026-09-14", 98.0, "tiingo"),
        ("2026-09-15", 99.0, "tiingo"),
        ("2026-09-16", 100.0, "alpha_vantage"),
        ("2026-09-17", 101.0, "alpha_vantage"),
        ("2026-09-18", 102.0, "alpha_vantage"),
    ]
    assert watermarks(db) == {"alpha_vantage": date(2026, 9, 18), "tiingo": date(2026, 9, 18)}
    assert (tmp_path / "data" / "raw" / date.today().isoformat() / SYMBOL / "tiingo.json").exists()


def test_overlapping_days_are_reconciled(db, tmp_path):
    result = tiingo_backfill.run_tiingo_backfill(SYMBOL, root=tmp_path, payload=TIINGO_PAYLOAD)

    reconciliation = result.reconciliation
    assert reconciliation.overlap_days == 3
    assert reconciliation.mismatched_days == 1
    assert reconciliation.max_diff_pct == pytest.approx(3.9604, abs=1e-4)
    assert "3 overlapping day(s), 1 beyond 0.5% close difference" in tiingo_backfill.format_result(result)


def test_rerun_inserts_nothing_and_daily_incremental_is_unaffected(db, tmp_path):
    tiingo_backfill.run_tiingo_backfill(SYMBOL, root=tmp_path, payload=TIINGO_PAYLOAD)
    before = bars(db)

    rerun = tiingo_backfill.run_tiingo_backfill(SYMBOL, root=tmp_path, payload=TIINGO_PAYLOAD)
    pipeline.run_stock(SYMBOL, root=tmp_path)

    assert rerun.inserted_rows == 0
    assert bars(db) == before
    with db() as conn:
        audits = conn.execute("SELECT source, record_count FROM load_metadata ORDER BY id").fetchall()
    assert audits == [("alpha_vantage", 3), ("tiingo", 2), ("tiingo", 0)]


def test_rejected_audit_rolls_back_the_backfill(db, tmp_path):
    with db() as conn:
        conn.execute("ALTER TABLE load_metadata ADD CONSTRAINT reject_tiingo CHECK (source <> 'tiingo')")

    with pytest.raises(psycopg.errors.CheckViolation):
        tiingo_backfill.run_tiingo_backfill(SYMBOL, root=tmp_path, payload=TIINGO_PAYLOAD)

    assert [source for _, _, source in bars(db)] == ["alpha_vantage"] * 3
    assert "tiingo" not in watermarks(db)
