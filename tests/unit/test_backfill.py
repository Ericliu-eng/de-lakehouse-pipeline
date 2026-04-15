from datetime import date

import pytest

from scripts.backfill import iter_dates, parse_date, run_backfill, validate_date_range


def test_parse_date_accepts_iso_date():
    result = parse_date("2026-01-01")

    assert result == date(2026, 1, 1)


def test_iter_dates_includes_start_and_end():
    result = list(iter_dates(date(2026, 1, 1), date(2026, 1, 3)))

    assert result == [
        date(2026, 1, 1),
        date(2026, 1, 2),
        date(2026, 1, 3),
    ]


def test_validate_date_range_rejects_start_after_end():
    with pytest.raises(ValueError, match="--start must be less than or equal to --end"):
        validate_date_range(date(2026, 1, 3), date(2026, 1, 1))


def test_run_backfill_returns_dates_to_process():
    result = run_backfill(date(2026, 1, 1), date(2026, 1, 2))

    assert result == [
        date(2026, 1, 1),
        date(2026, 1, 2),
    ]
