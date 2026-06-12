from __future__ import annotations

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from de_lakehouse_pipeline.transform.staging.staging_market_bars import (
    StagedMarketBar,
    stage_alpha_vantage_daily,
    staged_rows_to_db_tuples,
)


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
    rows = stage_alpha_vantage_daily(SAMPLE_ALPHA_VANTAGE_PAYLOAD)

    assert rows, "Parsed stock rows should not be empty"

    first_row = rows[0]

    assert isinstance(first_row, StagedMarketBar)
    assert first_row.ts == datetime(2026, 5, 28, tzinfo=ZoneInfo("US/Eastern"))
    assert first_row.symbol == "AAPL"
    assert first_row.open == 198.1
    assert first_row.high == 201.5
    assert first_row.low == 197.25
    assert first_row.close == 200.3
    assert first_row.volume == 1234567


@pytest.mark.smoke
def test_small_sample_stock_payload_returns_expected_tuple_shape() -> None:
    staged_rows = stage_alpha_vantage_daily(SAMPLE_ALPHA_VANTAGE_PAYLOAD)
    rows = staged_rows_to_db_tuples(staged_rows)

    for row in rows:
        assert isinstance(row, tuple)
        assert len(row) == 8


@pytest.mark.smoke
def test_core_pipeline_files_exist() -> None:
    required_paths = [
        Path("src/de_lakehouse_pipeline/backfill.py"),
        Path("src/de_lakehouse_pipeline/pipeline.py"),
        Path("src/de_lakehouse_pipeline/quality/checks.py"),
        Path("src/de_lakehouse_pipeline/load/metadata.py"),
        Path("src/de_lakehouse_pipeline/transform/staging/staging_market_bars.py"),
    ]

    missing_paths = [str(path) for path in required_paths if not path.exists()]

    assert not missing_paths, f"Missing required pipeline files: {missing_paths}"
