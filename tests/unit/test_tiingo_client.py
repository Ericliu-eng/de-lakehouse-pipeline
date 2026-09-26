from datetime import date
from unittest.mock import Mock, patch

import pytest

from de_lakehouse_pipeline.ingest import tiingo_client

GET = "de_lakehouse_pipeline.ingest.market_data_client.requests.get"


def response(payload):
    mock = Mock()
    mock.raise_for_status.return_value = None
    mock.json.return_value = payload
    return mock


def test_missing_token_raises(monkeypatch):
    monkeypatch.delenv("TIINGO_API_TOKEN", raising=False)

    with pytest.raises(ValueError, match="Missing TIINGO_API_TOKEN"):
        tiingo_client.fetch_tiingo_daily("AAPL")


def test_fetch_sends_token_in_header_not_url(monkeypatch):
    monkeypatch.setenv("TIINGO_API_TOKEN", "secret-token")
    bars = [{"date": "2026-09-18T00:00:00.000Z", "close": 1.0}]

    with patch(GET, return_value=response(bars)) as get:
        result = tiingo_client.fetch_tiingo_daily(" AAPL ", date(2000, 1, 3), date(2000, 1, 31))

    assert result == bars
    url = get.call_args.args[0]
    kwargs = get.call_args.kwargs
    assert url == "https://api.tiingo.com/tiingo/daily/aapl/prices"
    assert kwargs["params"] == {"startDate": "2000-01-03", "format": "json", "endDate": "2000-01-31"}
    assert kwargs["headers"] == {"Authorization": "Token secret-token"}
    assert "secret-token" not in url
    assert "secret-token" not in str(kwargs["params"])


def test_default_request_covers_full_history(monkeypatch):
    monkeypatch.setenv("TIINGO_API_TOKEN", "secret-token")

    with patch(GET, return_value=response([])) as get:
        tiingo_client.fetch_tiingo_daily("MSFT")

    assert get.call_args.kwargs["params"] == {"startDate": "1950-01-01", "format": "json"}


def test_non_list_response_is_rejected(monkeypatch):
    monkeypatch.setenv("TIINGO_API_TOKEN", "secret-token")

    with patch(GET, return_value=response({"detail": "Not found."})):
        with pytest.raises(ValueError, match="expected a list of daily bars"):
            tiingo_client.fetch_tiingo_daily("NOPE")
