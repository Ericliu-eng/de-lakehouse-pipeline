import pytest

from de_lakehouse_pipeline import pipeline


def test_run_stock_rejects_missing_volume_before_database(
    monkeypatch,
    tmp_path,
) -> None:
    payload = {
        "Meta Data": {
            "2. Symbol": "AAPL",
            "5. Time Zone": "UTC",
        },
        "Time Series (Daily)": {
            "2026-09-18": {
                "1. open": "100.0",
                "2. high": "110.0",
                "3. low": "95.0",
                "4. close": "105.0",
            }
        },
    }

    monkeypatch.setattr(
        pipeline,
        "fetch_daily_stock",
        lambda symbol: payload,
    )
    monkeypatch.setenv("ENABLE_S3_RAW_UPLOAD", "false")

    def fail_if_database_is_reached(*args, **kwargs):
        raise AssertionError("Database should not be reached")

    monkeypatch.setattr(
        pipeline,
        "wait_for_db",
        fail_if_database_is_reached,
    )

    with pytest.raises(ValueError, match="volume"):
        pipeline.run_stock(
            symbol="AAPL",
            root=tmp_path,
        )