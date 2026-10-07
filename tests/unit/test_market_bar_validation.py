from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from de_lakehouse_pipeline import pipeline, tiingo_backfill
from de_lakehouse_pipeline.quality import schema_validation as schema
from de_lakehouse_pipeline.transform.staging.staging_market_bars import (
    ALPHA_VANTAGE_FIELD_MAP,
    stage_alpha_vantage_daily,
    stage_tiingo_daily,
)


AS_OF = date(2026, 10, 6)
VALID = {"open": 100, "high": 110, "low": 90, "close": 105, "volume": 1000}


@pytest.fixture(autouse=True)
def market_clock(monkeypatch):
    monkeypatch.setattr(schema, "market_today", lambda: AS_OF)


def payload(source, fields, trading_date=AS_OF):
    if source == "alpha_vantage":
        return {
            "Meta Data": {"2. Symbol": "AAPL", "5. Time Zone": "US/Eastern"},
            "Time Series (Daily)": {
                trading_date.isoformat(): {
                    ALPHA_VANTAGE_FIELD_MAP[field]: str(value)
                    for field, value in fields.items()
                },
            },
        }
    return [{"date": trading_date.isoformat() + "T00:00:00.000Z", **fields}]


def stage(source, data):
    return stage_alpha_vantage_daily(data) if source == "alpha_vantage" else stage_tiingo_daily(data, "AAPL")


@pytest.mark.parametrize("source", ["alpha_vantage", "tiingo"])
@pytest.mark.parametrize("changes", [
    {"open": -1}, {"high": -1}, {"low": -1}, {"close": -1},
    {"open": "NaN"}, {"high": "Infinity"}, {"low": "-Infinity"}, {"close": "1e9999"},
    {"high": 99}, {"low": 106},
    {"volume": 1.9}, {"volume": -1}, {"volume": "NaN"}, {"volume": 2**63},
])
def test_both_sources_reject_invalid_ohlcv(source, changes):
    with pytest.raises(ValueError):
        stage(source, payload(source, {**VALID, **changes}))


@pytest.mark.parametrize("source", ["alpha_vantage", "tiingo"])
def test_future_trading_date_is_rejected(source):
    with pytest.raises(ValueError, match="future trading date"):
        stage(source, payload(source, VALID, AS_OF + timedelta(days=1)))


@pytest.mark.parametrize("source", ["alpha_vantage", "tiingo"])
def test_current_day_and_integer_volume_are_preserved(source):
    row = stage(source, payload(source, {**VALID, "volume": "1000.0"}))[0]
    assert row.ts.date() == AS_OF
    assert row.volume == 1000
    assert row.close == 105


@pytest.mark.parametrize("source", ["alpha_vantage", "tiingo"])
def test_invalid_data_stops_before_database_or_watermark(monkeypatch, tmp_path, source):
    data = payload(source, {**VALID, "close": "NaN"})

    def database_must_not_be_reached(*args, **kwargs):
        raise AssertionError("invalid data reached database configuration")

    monkeypatch.setenv("ENABLE_S3_RAW_UPLOAD", "false")
    if source == "alpha_vantage":
        monkeypatch.setattr(pipeline, "fetch_daily_stock", lambda symbol: data)
        monkeypatch.setattr(pipeline, "load_db_config", database_must_not_be_reached)
        def run():
            return pipeline.load_stock("AAPL", root=tmp_path)
    else:
        monkeypatch.setattr(tiingo_backfill, "load_db_config", database_must_not_be_reached)
        def run():
            return tiingo_backfill.run_tiingo_backfill("AAPL", root=tmp_path, payload=data)
    with pytest.raises(ValueError, match="finite"):
        run()


def test_timestamp_requires_timezone():
    with pytest.raises(ValueError, match="timezone-aware"):
        schema.validate_stock_row_schema({"symbol": "AAPL", "ts": datetime(2026, 10, 6), **VALID})


def test_historical_data_is_allowed():
    schema.validate_stock_row_schema({
        "symbol": "AAPL", "ts": datetime(1980, 12, 12, tzinfo=ZoneInfo("US/Eastern")), **VALID,
    })
