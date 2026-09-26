"""Tiingo end-of-day prices, used to backfill long price history."""
from __future__ import annotations

import os
from datetime import date

from dotenv import load_dotenv

from de_lakehouse_pipeline.ingest.market_data_client import fetch_json_with_retry

load_dotenv()

TIINGO_BASE_URL = "https://api.tiingo.com/tiingo/daily"
# Earlier than any listing Tiingo covers, so the default request returns full history.
DEFAULT_HISTORY_START = date(1950, 1, 1)


def get_tiingo_token() -> str:
    token = os.getenv("TIINGO_API_TOKEN")
    if not token:
        raise ValueError("Missing TIINGO_API_TOKEN")
    return token


def build_prices_url(symbol: str) -> str:
    return f"{TIINGO_BASE_URL}/{symbol.strip().lower()}/prices"


def fetch_tiingo_daily(
    symbol: str,
    start_date: date = DEFAULT_HISTORY_START,
    end_date: date | None = None,
) -> list[dict]:
    """Return daily bars for ``symbol``; one request covers the whole range."""
    params = {"startDate": start_date.isoformat(), "format": "json"}
    if end_date is not None:
        params["endDate"] = end_date.isoformat()

    # The token travels in a header so it never appears in request URLs or logs.
    payload = fetch_json_with_retry(
        params,
        url=build_prices_url(symbol),
        headers={"Authorization": f"Token {get_tiingo_token()}"},
    )
    if not isinstance(payload, list):
        raise ValueError(f"Unexpected Tiingo response for {symbol}: expected a list of daily bars")
    return payload
