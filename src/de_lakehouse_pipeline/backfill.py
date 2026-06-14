from __future__ import annotations

import argparse
from datetime import date, timedelta
import json
from pathlib import Path
from collections.abc import Iterator

from de_lakehouse_pipeline.pipeline import run_stock_for_date
from de_lakehouse_pipeline.load.db.stock_reader import load_completed_market_dates

CHECKPOINT_PATH = Path(".checkpoints/backfill_checkpoint.json")
DEFAULT_SYMBOL = "AAPL"

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

def run_backfill_for_date(target_date: date, symbol: str = DEFAULT_SYMBOL) -> None:
    print(f"Processing {target_date.isoformat()} for symbol={symbol}...")
    run_stock_for_date(target_date, symbol=symbol)


def sync_checkpoint_from_db(symbol: str) -> set[str]:
    checkpoint_dates = load_checkpoint()
    db_dates = load_completed_market_dates(symbol)
    #union / 并集 / 合并去重
    completed_dates = checkpoint_dates | db_dates
    save_checkpoint(completed_dates)

    return completed_dates
    
def run_backfill(start: date, end: date, symbol: str = DEFAULT_SYMBOL) -> None:
    completed_dates = sync_checkpoint_from_db(symbol)

    for target_date in iter_dates(start, end):
        if is_date_completed(target_date, completed_dates):
            print(f"Skipping {target_date.isoformat()} (already completed)")
            continue

        run_backfill_for_date(target_date, symbol=symbol)

        db_dates = load_completed_market_dates(symbol)
        if target_date.isoformat() in db_dates:
            mark_date_completed(target_date, completed_dates)
        else:
            print(
                f"Not marking {target_date.isoformat()} completed "
                f"because no DB row exists for symbol={symbol}"
            )



def load_checkpoint() -> set[str]:
    if not CHECKPOINT_PATH.exists():
        return set()

    with CHECKPOINT_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    completed_dates = data.get("completed_dates", [])
    return set(completed_dates)

def save_checkpoint(completed_dates: set[str]) -> None:
    CHECKPOINT_PATH.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "completed_dates": sorted(completed_dates)
    }

    with CHECKPOINT_PATH.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

def is_date_completed(target_date: date, completed_dates: set[str]) -> bool:
    return target_date.isoformat() in completed_dates

def mark_date_completed(target_date: date, completed_dates: set[str]) -> None:
    completed_dates.add(target_date.isoformat())
    save_checkpoint(completed_dates)



def main() -> None:
    args = parse_args()
    start = parse_iso_date(args.start)
    end = parse_iso_date(args.end)
    validate_date_range(start, end)
    run_backfill(start, end, symbol=args.symbol)

    
if __name__ == "__main__":
    main()
