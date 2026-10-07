from datetime import datetime, timedelta, timezone

import pytest

from de_lakehouse_pipeline.load.db.connection import connect, load_db_config, wait_for_db
from de_lakehouse_pipeline.observability.run_repository import (
    finish_pipeline_run,
    start_pipeline_run,
)

UTC = timezone.utc


@pytest.mark.integration
@pytest.mark.db
def test_pipeline_run_failure_round_trip() -> None:
    cfg = load_db_config()
    wait_for_db(cfg, timeout_s=10)
    conn = connect(cfg)

    try:
        started_at = datetime(2026, 9, 30, 18, 0, tzinfo=UTC)
        handle = start_pipeline_run(
            conn,
            pipeline_name="market_data_lakehouse_pipeline",
            source="tiingo",
            symbol="AAPL",
            started_at=started_at,
        )
        finish_pipeline_run(
            conn,
            run_id=handle.id,
            status="FAILED",
            quality_status="NOT_EVALUATED",
            finished_at=started_at + timedelta(seconds=3.25),
            error_type="TimeoutError",
            error_message="upstream request timed out",
        )

        row = conn.execute(
            """
            SELECT external_run_id,
                   status,
                   quality_status,
                   duration_ms,
                   rows_processed,
                   error_type,
                   error_message
            FROM pipeline_runs
            WHERE id = %s
            """,
            (handle.id,),
        ).fetchone()

        assert row == (
            handle.external_run_id,
            "FAILED",
            "NOT_EVALUATED",
            3250,
            0,
            "TimeoutError",
            "upstream request timed out",
        )
    finally:
        conn.rollback()
        conn.close()
