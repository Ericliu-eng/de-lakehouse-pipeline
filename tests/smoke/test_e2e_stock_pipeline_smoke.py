from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from de_lakehouse_pipeline.load.db.connection import connect, load_db_config
from de_lakehouse_pipeline.load.db.metadata_writer import insert_load_metadata
from de_lakehouse_pipeline.load.db.pipeline_metadata import upsert_watermark
from de_lakehouse_pipeline.load.db.stock_writer import upsert_stock_prices
from de_lakehouse_pipeline.load.metadata import record_load
from de_lakehouse_pipeline.quality.checks import (
    check_freshness,
    check_not_null,
    check_range,
)
from de_lakehouse_pipeline.transform.incremental import get_max_timestamp
from de_lakehouse_pipeline.transform.marts.mart_daily_symbol_summary import run_daily_summary
from de_lakehouse_pipeline.transform.marts.mart_symbol_latest_price import run_latest_price
from de_lakehouse_pipeline.transform.marts.mart_symbol_volume_rank import run_symbol_volume
from de_lakehouse_pipeline.transform.staging_market_bars import (
    stage_alpha_vantage_daily,
    staged_rows_to_db_tuples,
)

pytestmark = pytest.mark.db


SAMPLE_PAYLOAD = {
    "Meta Data": {
        "2. Symbol": "E2E_SMOKE",
        "5. Time Zone": "UTC",
    },
    "Time Series (Daily)": {
        "2026-04-07": {
            "1. open": "200.0000",
            "2. high": "215.0000",
            "3. low": "198.0000",
            "4. close": "210.0000",
            "5. volume": "2000",
        },
        "2026-04-06": {
            "1. open": "100.0000",
            "2. high": "112.0000",
            "3. low": "95.0000",
            "4. close": "110.0000",
            "5. volume": "1000",
        },
    },
}


@pytest.mark.smoke
def test_small_sample_runs_through_load_quality_and_marts() -> None:
    cfg = load_db_config()
    source = "e2e_smoke"
    symbol = "E2E_SMOKE"

    with connect(cfg) as conn:
        _clean_test_data(conn, source, symbol)

        try:
            staged_rows = stage_alpha_vantage_daily(SAMPLE_PAYLOAD)
            db_rows = staged_rows_to_db_tuples(staged_rows)

            upsert_stock_prices(conn, db_rows)
            upsert_watermark(
                conn,
                source,
                symbol,
                last_watermark=get_max_timestamp(db_rows),
                last_row_count=len(db_rows),
                status="success",
            )

            insert_load_metadata(
                conn,
                record_load(
                    source=source,
                    load_date="2026-04-07",
                    version="smoke-test",
                    record_count=len(db_rows),
                ),
            )

            quality_results = [
                check_not_null(conn, "market_bars", "symbol"),
                check_not_null(conn, "market_bars", "ts"),
                check_range(conn, "market_bars", "close", min_value=0),
                check_range(conn, "market_bars", "volume", min_value=0),
                check_freshness(conn, "market_bars", "ts", max_age_days=365),
            ]
            assert all(result.passed for result in quality_results)

            run_daily_summary(conn)
            run_latest_price(conn)
            run_symbol_volume(conn)
            conn.commit()

            assert _market_bar_count(conn, symbol) == 2
            assert _load_metadata_count(conn, source) >= 1
            assert _latest_snapshot(conn, symbol) == (
                datetime(2026, 4, 7, tzinfo=ZoneInfo("UTC")),
                210,
                2000,
            )
            assert _daily_summary(conn, symbol, "2026-04-06") == (110, 110, 110, 1000)
            assert _volume_rank(conn, symbol, "2026-04-07") is not None

        finally:
            _clean_test_data(conn, source, symbol)


def _market_bar_count(conn, symbol: str) -> int:
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM market_bars WHERE symbol = %s", (symbol,))
        return cur.fetchone()[0]


def _load_metadata_count(conn, source: str) -> int:
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM load_metadata WHERE source = %s", (source,))
        return cur.fetchone()[0]


def _latest_snapshot(conn, symbol: str) -> tuple:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT latest_ts, close_price, volume
            FROM mart_symbol_latest_price
            WHERE symbol = %s
            """,
            (symbol,),
        )
        return cur.fetchone()


def _daily_summary(conn, symbol: str, trading_date: str) -> tuple:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT avg_close, min_close, max_close, total_volume
            FROM mart_daily_symbol_summary
            WHERE symbol = %s AND trading_date = %s
            """,
            (symbol, trading_date),
        )
        return cur.fetchone()


def _volume_rank(conn, symbol: str, trading_date: str) -> int | None:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT volume_rank
            FROM mart_symbol_volume_rank
            WHERE symbol = %s AND trading_date = %s
            """,
            (symbol, trading_date),
        )
        row = cur.fetchone()
        return row[0] if row else None


def _clean_test_data(conn, source: str, symbol: str) -> None:
    with conn.cursor() as cur:
        cur.execute("DELETE FROM mart_symbol_volume_rank WHERE symbol = %s", (symbol,))
        cur.execute("DELETE FROM mart_daily_symbol_summary WHERE symbol = %s", (symbol,))
        cur.execute("DELETE FROM mart_symbol_latest_price WHERE symbol = %s", (symbol,))
        cur.execute("DELETE FROM market_bars WHERE symbol = %s", (symbol,))
        cur.execute("DELETE FROM pipeline_metadata WHERE source = %s AND symbol = %s", (source, symbol))
        cur.execute("DELETE FROM load_metadata WHERE source = %s", (source,))
    conn.commit()
