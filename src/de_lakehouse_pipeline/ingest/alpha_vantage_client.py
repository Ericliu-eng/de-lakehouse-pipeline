import os
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://www.alphavantage.co/query"

def fetch_daily_stock(symbol="AAPL")-> dict:

    api_key = os.getenv("ALPHA_VANTAGE_API_KEY")

    if not api_key:
        raise ValueError("Missing ALPHA_VANTAGE_API_KEY")

    param = {
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol,
        "apikey": api_key,
    }

    response = requests.get(BASE_URL, params=param)
    #If the HTTP status code is 200, nothing happens
    #If the status code is 4xx or 5xx, it raises an error
    response.raise_for_status()

    return response.json()



