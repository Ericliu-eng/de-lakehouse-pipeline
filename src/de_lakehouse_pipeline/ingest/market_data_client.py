import os
import time
#send http
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://www.alphavantage.co/query"


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

def fetch_json_with_retry(params: dict, max_retries: int = 3) -> dict:

    for attempt in range(max_retries + 1):
        try:
            response = requests.get(BASE_URL, params=params, timeout=20)
            response.raise_for_status()

            payload = response.json()

            if "Note" in payload:
                raise RuntimeError(payload["Note"])

            if "Error Message" in payload:
                raise ValueError(payload["Error Message"])

            return payload

        except (requests.Timeout, requests.ConnectionError, RuntimeError):
            if attempt == max_retries:
                raise

            sleep_time = 2 ** attempt
            time.sleep(sleep_time)

    raise RuntimeError("Failed to fetch stock data")

def fetch_daily_stock(symbol: str = "AAPL") -> dict:
    api_key = get_api_key()
    params = build_params(symbol, api_key)
    return fetch_json_with_retry(params)