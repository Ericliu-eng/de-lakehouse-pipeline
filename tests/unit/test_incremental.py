from datetime import datetime
from zoneinfo import ZoneInfo

from de_lakehouse_pipeline.transform.incremental import (
    filter_new_rows,
    get_max_timestamp,
)


def _row(ts: datetime, symbol: str = "AAPL") -> tuple:
    return (ts, symbol, 100.0, 110.0, 90.0, 105.0, 1000)


def test_filter_new_rows_when_watermark_is_none() -> None:
    rows = [
        _row(datetime(2026, 4, 1, tzinfo=ZoneInfo("UTC"))),
        _row(datetime(2026, 4, 2, tzinfo=ZoneInfo("UTC"))),
    ]

    assert filter_new_rows(rows, last_watermark=None) == rows


def test_filter_new_rows_only_keeps_rows_newer_than_watermark() -> None:
    rows = [
        _row(datetime(2026, 4, 1, tzinfo=ZoneInfo("UTC"))),
        _row(datetime(2026, 4, 2, tzinfo=ZoneInfo("UTC"))),
        _row(datetime(2026, 4, 3, tzinfo=ZoneInfo("UTC"))),
    ]

    new_rows = filter_new_rows(
        rows,
        last_watermark=datetime(2026, 4, 2, tzinfo=ZoneInfo("UTC")),
    )

    assert new_rows == [rows[2]]


def test_filter_new_rows_returns_empty_when_no_new_data() -> None:
    rows = [
        _row(datetime(2026, 4, 1, tzinfo=ZoneInfo("UTC"))),
        _row(datetime(2026, 4, 2, tzinfo=ZoneInfo("UTC"))),
    ]

    new_rows = filter_new_rows(
        rows,
        last_watermark=datetime(2026, 4, 2, tzinfo=ZoneInfo("UTC")),
    )

    assert new_rows == []


def test_get_max_timestamp_returns_latest_timestamp() -> None:
    rows = [
        _row(datetime(2026, 4, 1, tzinfo=ZoneInfo("UTC"))),
        _row(datetime(2026, 4, 3, tzinfo=ZoneInfo("UTC"))),
        _row(datetime(2026, 4, 2, tzinfo=ZoneInfo("UTC"))),
    ]

    result = get_max_timestamp(rows)

    assert result == datetime(2026, 4, 3, tzinfo=ZoneInfo("UTC"))


def test_get_max_timestamp_empty() -> None:
    assert get_max_timestamp([]) is None
