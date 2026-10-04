from datetime import date

import pytest

from de_lakehouse_pipeline import pipeline
from de_lakehouse_pipeline.symbols import normalize_symbol


@pytest.mark.parametrize("raw", ["AAPL", "aapl", "  aApL\n"])
def test_normalize_symbol_returns_one_business_key(raw) -> None:
    assert normalize_symbol(raw) == "AAPL"


@pytest.mark.parametrize("raw", [None, "", "   ", 123])
def test_normalize_symbol_rejects_missing_or_non_string(raw) -> None:
    with pytest.raises(ValueError, match="Missing stock symbol"):
        normalize_symbol(raw)


def _payload(symbol: str) -> dict:
    return {
        "Meta Data": {"2. Symbol": symbol, "5. Time Zone": "US/Eastern"},
        "Time Series (Daily)": {
            "2026-09-18": {
                "1. open": "100.0",
                "2. high": "100.0",
                "3. low": "100.0",
                "4. close": "100.0",
                "5. volume": "1000",
            }
        },
    }


def _fail_on_database(*args, **kwargs):
    raise AssertionError("the database must not be reached")


def test_mismatched_source_symbol_fails_before_raw_landing_or_database(
    monkeypatch, tmp_path
) -> None:
    # A provider answering for a different ticker must not be stored under the
    # requested one.
    monkeypatch.setattr(pipeline, "fetch_daily_stock", lambda symbol: _payload("MSFT"))
    monkeypatch.setattr(pipeline, "load_db_config", _fail_on_database)

    with pytest.raises(ValueError, match="does not match requested symbol"):
        pipeline.load_stock(symbol="AAPL", root=tmp_path)

    assert not (tmp_path / "data").exists()


def test_backfill_payload_for_another_symbol_is_rejected(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(pipeline, "load_db_config", _fail_on_database)

    with pytest.raises(ValueError, match="does not match requested symbol"):
        pipeline.run_stock_for_date(
            date(2026, 9, 18), symbol="aapl", root=tmp_path, payload=_payload("MSFT")
        )


def test_lowercase_request_lands_under_the_canonical_symbol(monkeypatch, tmp_path) -> None:
    requested: list[str] = []

    def fake_fetch(symbol: str) -> dict:
        requested.append(symbol)
        return _payload("AAPL")

    monkeypatch.setenv("ENABLE_S3_RAW_UPLOAD", "false")
    monkeypatch.setattr(pipeline, "fetch_daily_stock", fake_fetch)
    # Stop right after raw landing; this test is about the key, not the load.
    monkeypatch.setattr(pipeline, "stage_alpha_vantage_daily", lambda data: [])

    result = pipeline.load_stock(symbol=" aapl ", root=tmp_path)

    assert requested == ["AAPL"]
    assert result.raw_path.parent.name == "AAPL"
