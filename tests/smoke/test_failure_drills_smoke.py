import pytest

from de_lakehouse_pipeline.ingest.market_data_client import is_retryable_status_code
from de_lakehouse_pipeline.load.db.stock_writer import should_update_watermark_after_load
from de_lakehouse_pipeline.quality.schema_validation import validate_stock_row_schema


@pytest.mark.smoke
def test_reliability_drill_smoke_path():
    assert is_retryable_status_code(429) is True
    assert is_retryable_status_code(500) is True
    assert is_retryable_status_code(400) is False

    valid_row = {
        "symbol": "AAPL",
        "ts": "2026-06-18T00:00:00",
        "open": 190.0,
        "high": 195.0,
        "low": 188.0,
        "close": 193.0,
        "volume": 1000000,
    }

    validate_stock_row_schema(valid_row)

    with pytest.raises(ValueError, match="Missing required stock fields"):
        validate_stock_row_schema({"symbol": "AAPL"})

    assert should_update_watermark_after_load(load_success=True) is True
    assert should_update_watermark_after_load(load_success=False) is False