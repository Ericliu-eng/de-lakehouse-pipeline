from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest

from de_lakehouse_pipeline.observability.run_repository import (
    finish_pipeline_run,
    start_pipeline_run,
)

UTC = timezone.utc


class FakeCursor:
    def __init__(self, returned_row):
        self.returned_row = returned_row
        self.executed_sql = None
        self.executed_params = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def execute(self, sql, params):
        self.executed_sql = sql
        self.executed_params = params

    def fetchone(self):
        return self.returned_row


class FakeConnection:
    def __init__(self, returned_row):
        self.cursor_obj = FakeCursor(returned_row)

    def cursor(self):
        return self.cursor_obj


def test_start_pipeline_run_inserts_running_record() -> None:
    conn = FakeConnection((41,))
    started_at = datetime(2026, 9, 30, 18, 0, tzinfo=UTC)

    handle = start_pipeline_run(
        conn,
        pipeline_name=" market_data_lakehouse_pipeline ",
        source=" tiingo ",
        symbol=" AAPL ",
        started_at=started_at,
    )

    assert handle.id == 41
    assert isinstance(handle.external_run_id, UUID)
    assert "INSERT INTO pipeline_runs" in conn.cursor_obj.executed_sql
    assert conn.cursor_obj.executed_params == (
        "market_data_lakehouse_pipeline",
        handle.external_run_id,
        "tiingo",
        "AAPL",
        "RUNNING",
        started_at,
    )


def test_start_pipeline_run_rejects_empty_name() -> None:
    with pytest.raises(ValueError, match="pipeline_name"):
        start_pipeline_run(
            FakeConnection((1,)),
            pipeline_name="  ",
            started_at=datetime.now(UTC),
        )


def test_finish_pipeline_run_updates_terminal_fields() -> None:
    conn = FakeConnection((41,))
    finished_at = datetime(2026, 9, 30, 18, 1, tzinfo=UTC)

    finish_pipeline_run(
        conn,
        run_id=41,
        status="failed",
        quality_status="fail",
        finished_at=finished_at,
        rows_processed=12,
        error_type=" RuntimeError ",
        error_message=" upstream timeout ",
    )

    assert "UPDATE pipeline_runs" in conn.cursor_obj.executed_sql
    assert conn.cursor_obj.executed_params == (
        "FAILED",
        "FAIL",
        finished_at,
        finished_at,
        12,
        "RuntimeError",
        "upstream timeout",
        41,
    )


@pytest.mark.parametrize("status", ["RUNNING", "cancelled", ""])
def test_finish_pipeline_run_rejects_non_terminal_status(status) -> None:
    with pytest.raises(ValueError, match="status must be one of"):
        finish_pipeline_run(
            FakeConnection((1,)),
            run_id=1,
            status=status,
            finished_at=datetime.now(UTC),
        )


def test_finish_pipeline_run_rejects_negative_row_count() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        finish_pipeline_run(
            FakeConnection((1,)),
            run_id=1,
            status="success",
            finished_at=datetime.now(UTC) + timedelta(seconds=1),
            rows_processed=-1,
        )


def test_finish_pipeline_run_raises_when_run_is_missing() -> None:
    with pytest.raises(LookupError, match="pipeline run 99"):
        finish_pipeline_run(
            FakeConnection(None),
            run_id=99,
            status="failed",
            finished_at=datetime.now(UTC),
        )
