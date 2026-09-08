from dotenv import load_dotenv
from unittest.mock import patch,Mock
import pytest
import requests

#把 .env 文件内容变成 Python 可以用的环境变量
from de_lakehouse_pipeline.ingest.market_data_client import get_api_key,build_params,fetch_json_with_retry
load_dotenv()
#unit test
def test_get_api_key_when_env_exists() :
    with patch("de_lakehouse_pipeline.ingest.market_data_client.os.getenv",return_value = "fake-key"):
        result = get_api_key()
    assert result == "fake-key"
#unit test
def test_get_api_key_when_env_not_exists():
    with patch("de_lakehouse_pipeline.ingest.market_data_client.os.getenv", return_value=None):
        with pytest.raises(ValueError, match="Missing ALPHA_VANTAGE_API_KEY"):
            get_api_key()
#unit test  just check if Return the correct format.
def test_build_params_returns_expected_dict():
    result = build_params("AAPL", "fake-key")
    assert result == {
        "function": "TIME_SERIES_DAILY",
        "symbol": "AAPL",
        "apikey": "fake-key",
    }
#unit test check the fetch return 
def test_fetch_json_with_retry_returns_payload_on_success():
    expected = {
        "Meta Data": {"2. Symbol": "AAPL"},
        "Time Series (Daily)": {},
    }
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = expected

    with patch("de_lakehouse_pipeline.ingest.market_data_client.requests.get", return_value=mock_response) as mock_get:
        result = fetch_json_with_retry({"symbol": "AAPL"})

    assert result == expected
    assert mock_get.call_count == 1

#The API returns "Error Message".
#This should immediately raise a `ValueError` and not be retried.
def test_fetch_json_with_retry_raises_value_error_on_api_error():
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "Error Message": "Invalid API call."
    }
    with patch("de_lakehouse_pipeline.ingest.market_data_client.requests.get", return_value=mock_response):
        with pytest.raises(ValueError, match="Invalid API call."):
            fetch_json_with_retry({"symbol": "AAPL"})

#It keeps timing out, exceeding the maximum number of retries.
def test_fetch_json_with_retry_raises_after_max_retries():
    with patch(
        "de_lakehouse_pipeline.ingest.market_data_client.requests.get",
        side_effect=requests.Timeout("request timed out"),
    ) as mock_get:
        with patch("de_lakehouse_pipeline.ingest.market_data_client.time.sleep", return_value=None):
            with pytest.raises(requests.Timeout, match="request timed out"):
                fetch_json_with_retry({"symbol": "AAPL"}, max_retries=2)

    assert mock_get.call_count == 3


def http_response(status):
    response = requests.Response()
    response.status_code = status
    response._content = b'{"ok": true}'
    return response


@pytest.mark.parametrize("status", [429, 500, 502, 503, 504])
def test_http_transient_failure_retries_then_succeeds(status):
    with patch(
        "de_lakehouse_pipeline.ingest.market_data_client.requests.get",
        side_effect=[http_response(status), http_response(200)],
    ) as get, patch("de_lakehouse_pipeline.ingest.market_data_client.time.sleep") as sleep:
        assert fetch_json_with_retry({}) == {"ok": True}
    assert get.call_count == 2
    sleep.assert_called_once_with(1)


@pytest.mark.parametrize("status", [400, 401, 403, 404])
def test_http_permanent_failure_does_not_retry(status):
    with patch(
        "de_lakehouse_pipeline.ingest.market_data_client.requests.get",
        return_value=http_response(status),
    ) as get, patch("de_lakehouse_pipeline.ingest.market_data_client.time.sleep") as sleep:
        with pytest.raises(requests.HTTPError):
            fetch_json_with_retry({})
    assert get.call_count == 1
    sleep.assert_not_called()


@pytest.mark.parametrize("retries", [0, 2])
def test_http_retries_stop_at_budget(retries):
    with patch(
        "de_lakehouse_pipeline.ingest.market_data_client.requests.get",
        return_value=http_response(429),
    ) as get, patch("de_lakehouse_pipeline.ingest.market_data_client.time.sleep") as sleep:
        with pytest.raises(requests.HTTPError):
            fetch_json_with_retry({}, max_retries=retries)
    assert get.call_count == retries + 1
    assert [call.args[0] for call in sleep.call_args_list] == [2 ** i for i in range(retries)]

