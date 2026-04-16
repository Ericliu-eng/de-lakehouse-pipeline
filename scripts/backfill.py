from __future__ import annotations

import argparse
from datetime import date, timedelta


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


def main() -> None:
    args = parse_args()

    start_date = parse_iso_date(args.start)
    end_date = parse_iso_date(args.end)

    validate_date_range(start_date, end_date)

    print(f"Backfill requested from {start_date} to {end_date}")
    for run_date in iter_dates(start_date, end_date):
        print(f"Would process: {run_date}")


if __name__ == "__main__":
    main()