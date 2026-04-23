

import pytest

from de_lakehouse_pipeline.backfill import parse_iso_date, validate_date_range, iter_dates
from de_lakehouse_pipeline import backfill
from datetime import date

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

def test_load_checkpoint_returns_empty_set_when_file_missing(tmp_path, monkeypatch):
    checkpoint_path = tmp_path / "backfill_checkpoint.json"
    monkeypatch.setattr(backfill, "CHECKPOINT_PATH", checkpoint_path)

    result = backfill.load_checkpoint()

    assert result == set()

def test_save_and_load_checkpoint_round_trip(tmp_path, monkeypatch):
    checkpoint_path = tmp_path / "backfill_checkpoint.json"
    monkeypatch.setattr(backfill, "CHECKPOINT_PATH", checkpoint_path)

    completed_dates = {"2026-01-01", "2026-01-02"}
    backfill.save_checkpoint(completed_dates)

    loaded = backfill.load_checkpoint()

    assert loaded == completed_dates




def test_run_backfill_skips_completed_dates(tmp_path, monkeypatch):
    checkpoint_path = tmp_path / "backfill_checkpoint.json"
    monkeypatch.setattr(backfill, "CHECKPOINT_PATH", checkpoint_path)

    backfill.save_checkpoint({"2026-01-01"})

    processed = []

    def fake_run_backfill_for_date(target_date):
        processed.append(target_date.isoformat())

    monkeypatch.setattr(backfill, "run_backfill_for_date", fake_run_backfill_for_date)

    backfill.run_backfill(date(2026, 1, 1), date(2026, 1, 2))

    assert processed == ["2026-01-02"]
def test_run_backfill_marks_successful_dates_completed(tmp_path, monkeypatch):
    checkpoint_path = tmp_path / "backfill_checkpoint.json"
    monkeypatch.setattr(backfill, "CHECKPOINT_PATH", checkpoint_path)

    processed = []

    def fake_run_backfill_for_date(target_date):
        processed.append(target_date.isoformat())

    monkeypatch.setattr(backfill, "run_backfill_for_date", fake_run_backfill_for_date)

    backfill.run_backfill(date(2026, 1, 1), date(2026, 1, 2))

    loaded = backfill.load_checkpoint()

    assert processed == ["2026-01-01", "2026-01-02"]
    assert loaded == {"2026-01-01", "2026-01-02"}

def test_run_backfill_does_not_mark_failed_date_completed(tmp_path, monkeypatch):
    checkpoint_path = tmp_path / "backfill_checkpoint.json"
    monkeypatch.setattr(backfill, "CHECKPOINT_PATH", checkpoint_path)

    def fake_run_backfill_for_date(target_date):
        if target_date.isoformat() == "2026-01-02":
            raise RuntimeError("boom")

    monkeypatch.setattr(backfill, "run_backfill_for_date", fake_run_backfill_for_date)

    try:
        backfill.run_backfill(date(2026, 1, 1), date(2026, 1, 2))
    except RuntimeError:
        pass

    loaded = backfill.load_checkpoint()

    assert loaded == {"2026-01-01"}