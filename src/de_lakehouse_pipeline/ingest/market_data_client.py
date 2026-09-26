import os
import time
#requests 是 Python 里的一个库，用来发送 HTTP 请求。
import requests
#load .env
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://www.alphavantage.co/query"

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}

def get_api_key()  -> str:
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    if not api_key:
        raise ValueError("Missing ALPHA_VANTAGE_API_KEY")    
    return api_key
    
def build_params(symbol: str, api_key: str) -> dict:
    return {
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol,
        "apikey": api_key,
    }

def fetch_json_with_retry(
    params: dict,
    max_retries: int = 3,
    url: str = BASE_URL,
    headers: dict | None = None,
) -> dict | list:
    if max_retries < 0:
        raise ValueError("max_retries must be non-negative")
    for attempt in range(max_retries + 1):
        try:
            response = requests.get(url, params=params, headers=headers, timeout=20)
            response.raise_for_status()

            payload = response.json()
            # Provider-level error envelopes are JSON objects; list payloads
            # (for example Tiingo price history) are returned unchanged.
            if not isinstance(payload, dict):
                return payload

            if "Note" in payload:
                raise RuntimeError(payload["Note"])

            # Alpha Vantage may report throttling and subscription messages in
            # an HTTP 200 response under "Information" rather than "Note".
            if "Information" in payload:
                raise RuntimeError(payload["Information"])

            if "Error Message" in payload:
                raise ValueError(payload["Error Message"])

            return payload

        except requests.HTTPError as exc:
            if (
                exc.response is None
                or not is_retryable_status_code(exc.response.status_code)
                or attempt == max_retries
            ):
                raise
        except (requests.Timeout, requests.ConnectionError, RuntimeError):
            if attempt == max_retries:
                raise

        sleep_time = 2 ** attempt
        time.sleep(sleep_time)

    raise RuntimeError("Failed to fetch stock data")

def fetch_daily_stock(symbol: str = "AAPL") -> dict:
    api_key = get_api_key()
    params = build_params(symbol, api_key)
    payload = fetch_json_with_retry(params)
    required_keys = {"Meta Data", "Time Series (Daily)"}
    missing_keys = required_keys.difference(payload)
    if missing_keys:
        missing = ", ".join(sorted(missing_keys))
        raise ValueError(f"Alpha Vantage response is missing required keys: {missing}")
    return payload

def is_retryable_status_code(status_code: int) -> bool:
    """Return True if an HTTP status code should be retried."""
    return status_code in RETRYABLE_STATUS_CODES
