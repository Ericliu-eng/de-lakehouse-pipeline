from datetime import datetime, timezone

from de_lakehouse_pipeline.quality.reconciliation import reconcile_close_prices


def day(n: int) -> datetime:
    return datetime(2026, 9, n, tzinfo=timezone.utc)


def test_matching_overlap_passes():
    result = reconcile_close_prices({day(1): 100.0, day(2): 101.0}, {day(1): 100.0, day(2): 101.0})

    assert result.overlap_days == 2
    assert result.mismatched_days == 0
    assert result.max_diff_pct == 0
    assert result.passed


def test_only_shared_days_are_compared():
    result = reconcile_close_prices({day(1): 100.0, day(2): 50.0}, {day(1): 100.0, day(3): 10.0})

    assert result.overlap_days == 1
    assert result.passed


def test_difference_beyond_tolerance_is_counted():
    result = reconcile_close_prices(
        {day(1): 100.4, day(2): 102.0},
        {day(1): 100.0, day(2): 100.0},
        tolerance_pct=0.5,
    )

    assert result.overlap_days == 2
    assert result.mismatched_days == 1
    assert result.max_diff_pct == 2.0
    assert not result.passed


def test_no_overlap():
    result = reconcile_close_prices({day(1): 100.0}, {})

    assert result.overlap_days == 0
    assert result.max_diff_pct is None
    assert result.passed
