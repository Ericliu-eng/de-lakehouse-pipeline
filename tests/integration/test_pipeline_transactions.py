"""Exercise the real pipeline and PostgreSQL rollback in an isolated schema."""
from datetime import date
from pathlib import Path
from uuid import uuid4

import psycopg
from psycopg import sql
import pytest

from de_lakehouse_pipeline import pipeline
from de_lakehouse_pipeline.load.db.connection import connect, load_db_config

pytestmark = [pytest.mark.integration, pytest.mark.db]


@pytest.fixture
def isolated_connection(monkeypatch):
    cfg = load_db_config()
    schema = "test_atomic_" + uuid4().hex
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
        monkeypatch.setattr(pipeline, "connect", open_connection)
        monkeypatch.setattr(pipeline, "wait_for_db", lambda *args, **kwargs: None)
        yield open_connection
    finally:
        with connect(cfg) as conn:
            conn.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


@pytest.mark.parametrize("backfill", [False, True])
def test_audit_failure_rolls_back_and_retry_recovers(isolated_connection, monkeypatch, tmp_path, backfill):
    payload = {
        "Meta Data": {"2. Symbol": "ATOMIC", "5. Time Zone": "UTC"},
        "Time Series (Daily)": {
            "2026-01-05": {"1. open": "10", "2. high": "12", "3. low": "9",
                           "4. close": "11", "5. volume": "100"},
        },
    }
    monkeypatch.setattr(pipeline, "fetch_daily_stock", lambda symbol: payload)
    monkeypatch.setenv("ENABLE_S3_RAW_UPLOAD", "false")

    def run():
        if backfill:
            pipeline.run_stock_for_date(date(2026, 1, 5), symbol="ATOMIC", root=tmp_path)
        else:
            pipeline.run_stock(symbol="ATOMIC", root=tmp_path)

    # A real constraint failure occurs after the fact and watermark writes.
    with isolated_connection() as conn:
        conn.execute("ALTER TABLE load_metadata ADD CONSTRAINT reject_audit CHECK (record_count < 0)")
    with pytest.raises(psycopg.errors.CheckViolation):
        run()
    with isolated_connection() as conn:
        for table in ["market_bars", "pipeline_metadata", "load_metadata"]:
            assert conn.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(sql.Identifier(table))).fetchone()[0] == 0
        conn.execute("ALTER TABLE load_metadata DROP CONSTRAINT reject_audit")

    run()
    with isolated_connection() as conn:
        for table in ["market_bars", "pipeline_metadata", "load_metadata"]:
            assert conn.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(sql.Identifier(table))).fetchone()[0] == 1
        assert conn.execute("SELECT last_watermark::date FROM pipeline_metadata").fetchone()[0] == date(2026, 1, 5)
