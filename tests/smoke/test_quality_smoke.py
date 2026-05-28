from datetime import datetime
from zoneinfo import ZoneInfo
import pytest

from de_lakehouse_pipeline.load.db.connection import connect, load_db_config
from de_lakehouse_pipeline.load.db.stock_writer import upsert_stock_prices
from de_lakehouse_pipeline.quality.checks import (
    check_freshness,
    check_not_null,
    check_range,
)

@pytest.mark.smoke
def test_quality_checks_smoke_on_market_bars():
    cfg = load_db_config()
    symbol = "QUALITY_SMOKE"

    rows = [
        (
            datetime(2026, 4, 30, tzinfo=ZoneInfo("UTC")),
            symbol,
            100.0,
            110.0,
            90.0,
            105.0,
            1000,
        )
    ]

    with connect(cfg) as conn:
        _clean_test_data(conn, symbol)

        try:
            upsert_stock_prices(conn, rows)
            conn.commit()

            not_null_result = check_not_null(
                conn,
                table_name="market_bars",
                column_name="close",
            )

            range_result = check_range(
                conn,
                table_name="market_bars",
                column_name="close",
                min_value=0,
            )

            freshness_result = check_freshness(
                conn,
                table_name="market_bars",
                timestamp_column="ts",
                max_age_days=365,
            )

            assert not_null_result.passed is True
            assert range_result.passed is True
            assert freshness_result.passed is True

        finally:
            _clean_test_data(conn, symbol)

@pytest.mark.smoke
def _clean_test_data(conn, symbol: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM market_bars WHERE symbol = %s",
            (symbol,),
        )
    conn.commit()