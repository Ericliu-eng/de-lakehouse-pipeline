from __future__ import annotations

import json
from pathlib import Path

import pytest

from de_lakehouse_pipeline.transform.transform_stock import parse_alpha_vantage_daily


RAW_SAMPLE = Path("data/raw/2026-05-02/stock.json")


@pytest.mark.smoke
def test_small_sample_raw_stock_file_exists() -> None:
    assert RAW_SAMPLE.exists(), f"Missing raw sample file: {RAW_SAMPLE}"
    assert RAW_SAMPLE.is_file(), f"Expected a file, got: {RAW_SAMPLE}"
    assert RAW_SAMPLE.stat().st_size > 0, f"Raw sample file is empty: {RAW_SAMPLE}"


@pytest.mark.smoke
def test_small_sample_stock_json_can_be_loaded() -> None:
    with RAW_SAMPLE.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    assert isinstance(payload, dict)
    assert payload, "Raw stock JSON payload is empty"


@pytest.mark.smoke
def test_small_sample_stock_json_can_be_parsed() -> None:
    with RAW_SAMPLE.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    rows = parse_alpha_vantage_daily(payload)

    assert rows, "Parsed stock rows should not be empty"

    first_row = rows[0]

    # Your parser returns:
    # (
    #   ts,
    #   symbol,
    #   open,
    #   high,
    #   low,
    #   close,
    #   volume,
    # )
    assert isinstance(first_row, tuple)
    assert len(first_row) == 7

    ts, symbol, open_price, high, low, close, volume = first_row

    assert ts is not None
    assert symbol == "AAPL"
    assert isinstance(open_price, float)
    assert isinstance(high, float)
    assert isinstance(low, float)
    assert isinstance(close, float)
    assert isinstance(volume, int)


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