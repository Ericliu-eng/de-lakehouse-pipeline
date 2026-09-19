from __future__ import annotations

import argparse
from datetime import date, timedelta
import json
import os
import tempfile
from pathlib import Path
from collections.abc import Iterator

from de_lakehouse_pipeline.pipeline import run_stock_for_date
from de_lakehouse_pipeline.ingest.market_data_client import fetch_daily_stock
from de_lakehouse_pipeline.load.db.stock_reader import load_completed_market_dates

CHECKPOINT_PATH = Path(".checkpoints/backfill_checkpoint.json")
DEFAULT_SYMBOL = "AAPL"
DEFAULT_SOURCE = "alpha_vantage"

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run backfill for a date range.")
    parser.add_argument("--start", required=True, help="Start date in YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="End date in YYYY-MM-DD")
    parser.add_argument("--symbol", default=DEFAULT_SYMBOL, help="Stock symbol to backfill")
    return parser.parse_args()


def parse_iso_date(value: str) -> date:
    return date.fromisoformat(value)


def validate_date_range(start_date: date, end_date: date) -> None:
    if start_date > end_date:
        raise ValueError("start date must be on or before end date")


def iter_dates(start: date, end: date) -> Iterator[date]:
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)

def run_backfill_for_date(
    target_date: date,
    symbol: str = DEFAULT_SYMBOL,
    payload: dict | None = None,
) -> None:
    print(f"Processing {target_date.isoformat()} for symbol={symbol}...")
    run_stock_for_date(target_date, symbol=symbol, payload=payload)


def sync_checkpoint_from_db(symbol: str) -> set[str]:
    db_dates = load_completed_market_dates(symbol)
    # PostgreSQL is authoritative; stale local dates must not hide missing rows.
    completed_dates = db_dates
    save_checkpoint(completed_dates, symbol=symbol)

    return completed_dates
    
def run_backfill(start: date, end: date, symbol: str = DEFAULT_SYMBOL) -> None:
    validate_date_range(start, end)
    symbol = symbol.strip().upper()
    if not symbol:
        raise ValueError("symbol must not be empty")
    completed_dates = sync_checkpoint_from_db(symbol)

    pending_dates = [
        target_date
        for target_date in iter_dates(start, end)
        if not is_date_completed(target_date, completed_dates)
    ]
    if not pending_dates:
        print(f"No incomplete dates for symbol={symbol}")
        return

    # TIME_SERIES_DAILY returns a multi-date payload, so fetch it once and
    # reuse it for every pending date instead of consuming one API call per day.
    payload = fetch_daily_stock(symbol)

    for target_date in iter_dates(start, end):
        if is_date_completed(target_date, completed_dates):
            print(f"Skipping {target_date.isoformat()} (already completed)")
            continue

        run_backfill_for_date(target_date, symbol=symbol, payload=payload)

        db_dates = load_completed_market_dates(symbol)
        if target_date.isoformat() in db_dates:
            mark_date_completed(target_date, completed_dates, symbol=symbol)
        else:
            print(
                f"Not marking {target_date.isoformat()} completed "
                f"because no DB row exists for symbol={symbol}"
            )



def load_checkpoint(symbol: str = DEFAULT_SYMBOL, source: str = DEFAULT_SOURCE) -> set[str]:
    if not CHECKPOINT_PATH.exists():
        return set()

    with CHECKPOINT_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # Legacy unscoped dates cannot safely be attributed to any stock.
    completed_dates = data.get(source, {}).get(symbol.strip().upper(), [])
    return set(completed_dates)

def save_checkpoint(
    completed_dates: set[str], symbol: str = DEFAULT_SYMBOL, source: str = DEFAULT_SOURCE
) -> None:
    CHECKPOINT_PATH.parent.mkdir(parents=True, exist_ok=True)

    payload = {}
    if CHECKPOINT_PATH.exists():
        payload = json.loads(CHECKPOINT_PATH.read_text(encoding="utf-8"))
    payload.pop("completed_dates", None)
    payload.setdefault(source, {})[symbol.strip().upper()] = sorted(completed_dates)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=CHECKPOINT_PATH.parent, delete=False
        ) as f:
            temp_path = Path(f.name)
            json.dump(payload, f, indent=2)
        os.replace(temp_path, CHECKPOINT_PATH)
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)

def is_date_completed(target_date: date, completed_dates: set[str]) -> bool:
    return target_date.isoformat() in completed_dates

def mark_date_completed(
    target_date: date, completed_dates: set[str], symbol: str = DEFAULT_SYMBOL
) -> None:
    completed_dates.add(target_date.isoformat())
    save_checkpoint(completed_dates, symbol=symbol)



def main() -> None:
    args = parse_args()
    start = parse_iso_date(args.start)
    end = parse_iso_date(args.end)
    validate_date_range(start, end)
    run_backfill(start, end, symbol=args.symbol)

    
if __name__ == "__main__":
    main()
