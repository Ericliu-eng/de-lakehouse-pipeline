from datetime import datetime
from zoneinfo import ZoneInfo

from de_lakehouse_pipeline.load.db.connection import connect, load_db_config
from de_lakehouse_pipeline.load.db.pipeline_metadata import (
    get_last_watermark,
    upsert_watermark,
)
from de_lakehouse_pipeline.load.db.stock_writer import upsert_stock_prices
from de_lakehouse_pipeline.transform.incremental import (
    filter_new_rows,
    get_max_timestamp,
)


def test_incremental_behavior():
    cfg = load_db_config()

    rows = [
        (
            datetime(2026, 4, 1, tzinfo=ZoneInfo("UTC")),
            "SMOKE",
            100.0,
            110.0,
            90.0,
            105.0,
            1000,
        ),
        (
            datetime(2026, 4, 2, tzinfo=ZoneInfo("UTC")),
            "SMOKE",
            105.0,
            115.0,
            95.0,
            108.0,
            1200,
        ),
    ]

    source = "smoke_test"
    symbol = "SMOKE"

    with connect(cfg) as conn:
        _clean_test_data(conn, source, symbol)

        last_watermark = get_last_watermark(conn, source, symbol)
        first_batch = filter_new_rows(rows, last_watermark)

        assert len(first_batch) == 2

        upsert_stock_prices(conn, first_batch)
        upsert_watermark(
            conn,
            source,
            symbol,
            last_watermark=get_max_timestamp(first_batch),
            last_row_count=len(first_batch),
            status="success",
        )

        first_count = _count_market_rows(conn, symbol)
        first_watermark = get_last_watermark(conn, source, symbol)

        assert first_count == 2
        assert first_watermark == datetime(2026, 4, 2, tzinfo=ZoneInfo("UTC"))

        second_last_watermark = get_last_watermark(conn, source, symbol)
        second_batch = filter_new_rows(rows, second_last_watermark)

        assert second_batch == []

        if second_batch:
            upsert_stock_prices(conn, second_batch)
            upsert_watermark(
                conn,
                source,
                symbol,
                last_watermark=get_max_timestamp(second_batch),
                last_row_count=len(second_batch),
                status="success",
            )

        second_count = _count_market_rows(conn, symbol)
        second_watermark = get_last_watermark(conn, source, symbol)

        assert second_count == first_count
        assert second_watermark == first_watermark

        _clean_test_data(conn, source, symbol)


def _count_market_rows(conn, symbol: str) -> int:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM market_bars WHERE symbol = %s",
            (symbol,),
        )
        return cur.fetchone()[0]


def _clean_test_data(conn, source: str, symbol: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM market_bars WHERE symbol = %s",
            (symbol,),
        )
        cur.execute(
            """
            DELETE FROM pipeline_metadata
            WHERE source = %s AND symbol = %s
            """,
            (source, symbol),
        )
    conn.commit()
