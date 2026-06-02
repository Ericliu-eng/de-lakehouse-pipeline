from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from de_lakehouse_pipeline.transform.staging.staging_market_bars import (
    StagedMarketBar,
    stage_alpha_vantage_daily,
    staged_rows_to_db_tuples,
    to_db_tuple,
)


SAMPLE_PAYLOAD = {
    "Meta Data": {
        "2. Symbol": " aapl ",
        "5. Time Zone": "US/Eastern",
    },
    "Time Series (Daily)": {
        "2026-05-28": {
            "1. open": "198.1000",
            "2. high": "201.5000",
            "3. low": "197.2500",
            "4. close": "200.3000",
            "5. volume": "1234567",
        }
    },
}


def test_stage_alpha_vantage_daily_returns_typed_market_bar() -> None:
    rows = stage_alpha_vantage_daily(SAMPLE_PAYLOAD)

    assert rows == [
        StagedMarketBar(
            ts=datetime(2026, 5, 28, tzinfo=ZoneInfo("US/Eastern")),
            symbol="AAPL",
            open=198.1,
            high=201.5,
            low=197.25,
            close=200.3,
            volume=1234567,
        )
    ]


def test_stage_alpha_vantage_daily_requires_symbol() -> None:
    payload = {
        "Meta Data": {
            "5. Time Zone": "US/Eastern",
        },
        "Time Series (Daily)": {},
    }

    with pytest.raises(ValueError, match="Missing stock symbol"):
        stage_alpha_vantage_daily(payload)


def test_to_db_tuple_preserves_market_bars_column_order() -> None:
    ts = datetime(2026, 5, 28, tzinfo=ZoneInfo("US/Eastern"))
    row = StagedMarketBar(
        ts=ts,
        symbol="AAPL",
        open=198.1,
        high=201.5,
        low=197.25,
        close=200.3,
        volume=1234567,
    )

    assert to_db_tuple(row) == (
        ts,
        "AAPL",
        198.1,
        201.5,
        197.25,
        200.3,
        1234567,
    )


def test_staged_rows_to_db_tuples_converts_all_rows() -> None:
    rows = stage_alpha_vantage_daily(SAMPLE_PAYLOAD)

    assert staged_rows_to_db_tuples(rows) == [to_db_tuple(rows[0])]
