import os
import time
#send http
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://www.alphavantage.co/query"


def fetch_daily_stock(symbol="AAPL") -> dict:

    api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    if not api_key:
        raise ValueError("Missing ALPHA_VANTAGE_API_KEY")
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol,
        "apikey": api_key,
    }

    max_retries = 3

    for attempt in range(max_retries + 1):
        try:
            # send https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=AAPL&apikey=3MY6ED9KVGJJCYSS
            response = requests.get(BASE_URL, params=params, timeout=20)
            response.raise_for_status()
            payload = response.json()

            # AlphaVantage rate limit
            if "Note" in payload:
                raise RuntimeError(payload["Note"])

            # API error
            if "Error Message" in payload:
                raise ValueError(payload["Error Message"])

            return payload

        except (requests.Timeout, requests.ConnectionError, RuntimeError) as e:
            print(f"Fetch failed: {e}")
            if attempt == max_retries:
                raise

            sleep_time = 2 ** attempt
            time.sleep(sleep_time)

    raise RuntimeError("Failed to fetch stock data")