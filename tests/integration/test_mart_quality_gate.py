from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import pytest
from psycopg import sql

from de_lakehouse_pipeline import cli
from de_lakehouse_pipeline.load.db.connection import connect, load_db_config
from de_lakehouse_pipeline.quality.checks import check_freshness
from de_lakehouse_pipeline.quality.schema_validation import market_today


pytestmark = [pytest.mark.integration, pytest.mark.db]


@pytest.fixture
def warehouse(monkeypatch):
    cfg = load_db_config()
    schema = "test_mart_gate_" + uuid4().hex
    with connect(cfg) as conn:
        conn.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))

    def open_connection(_cfg=None):
        conn = connect(cfg)
        conn.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(schema)))
        conn.commit()
        return conn

    try:
        root = Path(__file__).resolve().parents[2]
        with open_connection() as conn:
            for name in ["003_market_bars.sql", "005_marts.sql", "008_add_source_to_market_bars.sql"]:
                conn.execute((root / "migrations" / name).read_text(encoding="utf-8"))
            conn.execute(
                "INSERT INTO mart_symbol_latest_price (symbol, latest_ts, close_price, volume) "
                "VALUES ('AAPL', '2000-01-03 00:00:00+00', 99, 10)"
            )
        monkeypatch.setattr(cli, "connect", open_connection)
        monkeypatch.setattr(cli, "wait_for_db", lambda *args, **kwargs: None)
        yield open_connection
    finally:
        with connect(cfg) as conn:
            conn.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


def insert_bar(warehouse, **changes):
    row = {
        "ts": datetime(2000, 1, 3, tzinfo=timezone.utc),
        "open": 10, "high": 12, "low": 9, "close": 11, "volume": 100,
        **changes,
    }
    with warehouse() as conn:
        conn.execute(
            "INSERT INTO market_bars (ts, symbol, open, high, low, close, volume, source) "
            "VALUES (%s, 'AAPL', %s, %s, %s, %s, %s, 'tiingo')",
            tuple(row[key] for key in ["ts", "open", "high", "low", "close", "volume"]),
        )


@pytest.mark.parametrize("changes", [
    {"open": -1}, {"close": "NaN"}, {"high": "Infinity"}, {"low": "-Infinity"},
    {"open": None}, {"volume": None}, {"volume": -1}, {"high": 8},
    {"ts": datetime.now(timezone.utc) + timedelta(days=2)},
])
def test_manual_marts_reject_invalid_existing_data_without_publishing(warehouse, changes):
    insert_bar(warehouse, **changes)
    with pytest.raises(RuntimeError, match="market_bar_values"):
        cli.run_marts()
    with warehouse() as conn:
        assert conn.execute("SELECT close_price FROM mart_symbol_latest_price").fetchone()[0] == 99
        assert conn.execute("SELECT COUNT(*) FROM mart_daily_symbol_summary").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM mart_symbol_volume_rank").fetchone()[0] == 0


def test_manual_marts_allow_valid_historical_backfill(warehouse):
    insert_bar(warehouse)
    cli.run_marts()
    with warehouse() as conn:
        assert conn.execute("SELECT close_price FROM mart_symbol_latest_price").fetchone()[0] == 11
        assert conn.execute("SELECT COUNT(*) FROM mart_daily_symbol_summary").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM mart_symbol_volume_rank").fetchone()[0] == 1


def test_future_freshness_fails_in_postgres(warehouse):
    insert_bar(warehouse, ts=datetime.now(timezone.utc) + timedelta(days=2))
    with warehouse() as conn:
        result = check_freshness(conn, "market_bars", "ts", max_age_days=14)
    assert not result.passed


def test_freshness_uses_market_date_instead_of_session_timezone(warehouse):
    # New York midnight is still the previous calendar day at UTC-12.
    midnight = market_today().isoformat() + " 00:00:00 America/New_York"
    insert_bar(warehouse, ts=midnight)
    with warehouse() as conn:
        conn.execute("SET TIME ZONE INTERVAL '-12:00' HOUR TO MINUTE")
        result = check_freshness(conn, "market_bars", "ts", max_age_days=0)
    assert result.passed
