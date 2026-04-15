from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta


def parse_date(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"Invalid date '{value}'. Expected format: YYYY-MM-DD."
        ) from exc


def iter_dates(start: date, end: date):
    current = start

    while current <= end:
        yield current
        current += timedelta(days=1)


def validate_date_range(start: date, end: date) -> None:
    if start > end:
        raise ValueError("--start must be less than or equal to --end")


def run_backfill(start: date, end: date) -> list[date]:
    validate_date_range(start, end)

    dates = list(iter_dates(start, end))

    for run_date in dates:
        print(f"Backfill scaffold: would process {run_date.isoformat()}")

    return dates


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Backfill scaffold for historical pipeline runs."
    )
    parser.add_argument("--start", required=True, type=parse_date)
    parser.add_argument("--end", required=True, type=parse_date)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    run_backfill(args.start, args.end)


if __name__ == "__main__":
    main()
