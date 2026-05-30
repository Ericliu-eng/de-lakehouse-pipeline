import pytest
from datetime import datetime
from zoneinfo import ZoneInfo
from de_lakehouse_pipeline.load.db.connection import load_db_config, connect
from de_lakehouse_pipeline.transform.marts.mart_daily_symbol_summary import run_daily_summary
from de_lakehouse_pipeline.transform.marts.mart_symbol_latest_price import run_latest_price
from de_lakehouse_pipeline.transform.marts.mart_symbol_volume_rank import run_symbol_volume

pytestmark = [pytest.mark.integration, pytest.mark.db]


@pytest.fixture
def db_conn():
    config = load_db_config()
    conn = connect(config)
    try:
        yield conn
    finally:
        conn.rollback()
        conn.close()

def seed_market_bars(conn):
    with conn.cursor() as cur:
        cur.execute("DELETE FROM mart_symbol_volume_rank WHERE trading_date = %s", ("2026-04-06",))
        cur.execute("DELETE FROM mart_daily_symbol_summary WHERE trading_date = %s", ("2026-04-06",))
        cur.execute("DELETE FROM mart_symbol_latest_price WHERE symbol IN (%s, %s)", ("TESTA", "TESTB"))
        cur.execute("DELETE FROM market_bars WHERE ts::date = %s", ("2026-04-06",))

        cur.execute(
            """
            INSERT INTO market_bars (ts, symbol, open, high, low, close, volume)
            VALUES
                (%s, 'TESTA', 10, 12, 9, 11, 100),
                (%s, 'TESTA', 11, 13, 10, 12, 200),
                (%s, 'TESTB', 20, 22, 19, 21, 50),
                (%s, 'TESTB', 21, 23, 20, 22, 70)
            """,
            (
                datetime(2026, 4, 6, 10, 0, tzinfo=ZoneInfo("UTC")),
                datetime(2026, 4, 6, 11, 0, tzinfo=ZoneInfo("UTC")),
                datetime(2026, 4, 6, 10, 0, tzinfo=ZoneInfo("UTC")),
                datetime(2026, 4, 6, 11, 0, tzinfo=ZoneInfo("UTC")),
            ),
        )
    conn.commit()

def test_summary_aggregates(db_conn):
    seed_market_bars(db_conn)
    run_daily_summary(db_conn)

    with db_conn.cursor() as cur:
        cur.execute(
            """
            SELECT avg_close, min_close, max_close, total_volume
            FROM mart_daily_symbol_summary
            WHERE symbol = %s AND trading_date = %s
            """,
            ("TESTA", "2026-04-06"),
        )
        row = cur.fetchone()

    assert row is not None
    assert row[0] == 11.5
    assert row[1] == 11
    assert row[2] == 12
    assert row[3] == 300


def test_latest_price_is_most_recent(db_conn):
    seed_market_bars(db_conn)

    run_latest_price(db_conn)

    with db_conn.cursor() as cur:
        cur.execute(
            """
            SELECT latest_ts, close_price, volume
            FROM mart_symbol_latest_price
            WHERE symbol = %s
            """,
            ("TESTA",),
        )
        row = cur.fetchone()

    expected_ts = datetime(2026, 4, 6, 11, 0, tzinfo=ZoneInfo("UTC"))
    assert row is not None
    assert row[0] == expected_ts
    assert row[1] == 12
    assert row[2] == 200

def test_volume_rank_order(db_conn):
    seed_market_bars(db_conn)

    run_daily_summary(db_conn)
    run_symbol_volume(db_conn)

    with db_conn.cursor() as cur:
        cur.execute(
            """
            SELECT symbol, total_volume, volume_rank
            FROM mart_symbol_volume_rank
            WHERE trading_date = %s
            ORDER BY volume_rank ASC
            """,
            ("2026-04-06",),
        )
        rows = cur.fetchall()

    assert len(rows) >= 2
    assert rows[0][0] == "TESTA"
    assert rows[0][1] == 300
    assert rows[1][0] == "TESTB"
    assert rows[1][1] == 120
    assert rows[0][1] >= rows[1][1]


def test_marts_are_idempotent_on_rerun(db_conn):
    seed_market_bars(db_conn)

    run_daily_summary(db_conn)
    run_latest_price(db_conn)
    run_symbol_volume(db_conn)
    run_daily_summary(db_conn)
    run_latest_price(db_conn)
    run_symbol_volume(db_conn)

    with db_conn.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(*)
            FROM mart_daily_symbol_summary
            WHERE trading_date = %s AND symbol IN (%s, %s)
            """,
            ("2026-04-06", "TESTA", "TESTB"),
        )
        daily_count = cur.fetchone()[0]

        cur.execute(
            """
            SELECT COUNT(*)
            FROM mart_symbol_latest_price
            WHERE symbol IN (%s, %s)
            """,
            ("TESTA", "TESTB"),
        )
        latest_count = cur.fetchone()[0]

        cur.execute(
            """
            SELECT COUNT(*)
            FROM mart_symbol_volume_rank
            WHERE trading_date = %s AND symbol IN (%s, %s)
            """,
            ("2026-04-06", "TESTA", "TESTB"),
        )
        rank_count = cur.fetchone()[0]

    assert daily_count == 2
    assert latest_count == 2
    assert rank_count == 2
