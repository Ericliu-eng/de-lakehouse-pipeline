import pytest

from de_lakehouse_pipeline.ingest.market_data_client import is_retryable_status_code
from de_lakehouse_pipeline.load.db.stock_writer import should_update_watermark_after_load
from de_lakehouse_pipeline.quality.schema_validation import validate_stock_row_schema

def test_valid_stock_row_schema_passes():
    row = {
        "symbol": "AAPL",
        "ts": "2026-06-16T00:00:00",
        "open": 0.0,
        "high": 0.0,
        "low": 0.0,
        "close": 0.0,
        "volume": 1000000,
    }

    validate_stock_row_schema(row)


def test_missing_required_stock_field_fails():
    row = {
        "symbol": "AAPL",
        "ts": "2026-06-16T00:00:00",
        "open": 190.0,
    }

    with pytest.raises(ValueError, match="Missing required stock fields"):
        validate_stock_row_schema(row)

def test_watermark_should_not_update_when_load_fails():
    assert should_update_watermark_after_load(load_success=False) is False


def test_watermark_should_update_when_load_succeeds():
    assert should_update_watermark_after_load(load_success=True) is True

    

def test_api_429_is_retryable():
    assert is_retryable_status_code(429) is True


def test_api_500_is_retryable():
    assert is_retryable_status_code(500) is True


def test_api_400_is_not_retryable():
    assert is_retryable_status_code(400) is False
