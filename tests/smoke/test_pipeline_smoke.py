from __future__ import annotations

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from de_lakehouse_pipeline.transform.transform_stock import parse_alpha_vantage_daily


SAMPLE_ALPHA_VANTAGE_PAYLOAD = {
    "Meta Data": {
        "2. Symbol": "AAPL",
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


@pytest.mark.smoke
def test_small_sample_stock_payload_can_be_parsed() -> None:
    rows = parse_alpha_vantage_daily(SAMPLE_ALPHA_VANTAGE_PAYLOAD)

    assert rows, "Parsed stock rows should not be empty"

    first_row = rows[0]

    assert isinstance(first_row, tuple)
    assert len(first_row) == 7

    ts, symbol, open_price, high, low, close, volume = first_row

    assert ts == datetime(2026, 5, 28, tzinfo=ZoneInfo("US/Eastern"))
    assert symbol == "AAPL"
    assert open_price == 198.1
    assert high == 201.5
    assert low == 197.25
    assert close == 200.3
    assert volume == 1234567


@pytest.mark.smoke
def test_small_sample_stock_payload_returns_expected_tuple_shape() -> None:
    rows = parse_alpha_vantage_daily(SAMPLE_ALPHA_VANTAGE_PAYLOAD)

    for row in rows:
        assert isinstance(row, tuple)
        assert len(row) == 7


@pytest.mark.smoke
def test_core_pipeline_files_exist() -> None:
    required_paths = [
        Path("src/de_lakehouse_pipeline/backfill.py"),
        Path("src/de_lakehouse_pipeline/pipeline.py"),
        Path("src/de_lakehouse_pipeline/quality/checks.py"),
        Path("src/de_lakehouse_pipeline/load/metadata.py"),
    ]

    missing_paths = [str(path) for path in required_paths if not path.exists()]

    assert not missing_paths, f"Missing required pipeline files: {missing_paths}"