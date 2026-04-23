from __future__ import annotations

import argparse
from datetime import date, timedelta
import json
from pathlib import Path
from de_lakehouse_pipeline.pipeline import run_stock_for_date

CHECKPOINT_PATH = Path(".checkpoints/backfill_checkpoint.json")

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run backfill for a date range.")
    parser.add_argument("--start", required=True, help="Start date in YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="End date in YYYY-MM-DD")
    return parser.parse_args()


def parse_iso_date(value: str) -> date:
    return date.fromisoformat(value)


def validate_date_range(start_date: date, end_date: date) -> None:
    if start_date > end_date:
        raise ValueError("start date must be on or before end date")


def iter_dates(start: date, end: date):
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)

def run_backfill_for_date(target_date: date) -> None:
    print(f"Processing {target_date.isoformat()}...")
    run_stock_for_date(target_date, symbol="AAPL")


def run_backfill(start: date, end: date) -> None:
    completed_dates = load_checkpoint()

    for target_date in iter_dates(start, end):
        if is_date_completed(target_date, completed_dates):
            print(f"Skipping {target_date.isoformat()} (already completed)")
            continue

        run_backfill_for_date(target_date)
        mark_date_completed(target_date, completed_dates)

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
    run_backfill(start, end)

    
if __name__ == "__main__":
    main()