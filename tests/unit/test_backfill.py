from datetime import date

import pytest

from scripts.backfill import parse_iso_date, validate_date_range, iter_dates


def test_parse_iso_date_returns_date_object():
    result = parse_iso_date("2026-01-01")
    assert result == date(2026, 1, 1)


def test_iter_dates_includes_start_and_end():
    result = list(iter_dates(date(2026, 1, 1), date(2026, 1, 3)))
    assert result == [
        date(2026, 1, 1),
        date(2026, 1, 2),
        date(2026, 1, 3),
    ]


def test_validate_date_range_allows_same_start_and_end():
    validate_date_range(date(2026, 1, 1), date(2026, 1, 1))


def test_validate_date_range_raises_for_invalid_range():
    with pytest.raises(ValueError, match="start date must be on or before end date"):
        validate_date_range(date(2026, 1, 7), date(2026, 1, 1))