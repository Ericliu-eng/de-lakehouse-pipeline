from uuid import uuid4

import pytest

from de_lakehouse_pipeline.load.db.connection import connect, load_db_config, wait_for_db
from orchestration import dagster_pipeline as runner


@pytest.mark.integration
@pytest.mark.db
@pytest.mark.parametrize(
    (
        "failure_step",
        "expected_status",
        "expected_quality",
        "expected_error_type",
        "expected_error_fragment",
    ),
    [
        (None, "SUCCESS", "PASS", None, None),
        ("ingest", "FAILED", "NOT_EVALUATED", "RuntimeError", "provider failure"),
        ("quality", "FAILED", "FAIL", "RuntimeError", "quality failure"),
    ],
)
def test_orchestrated_pipeline_persists_terminal_run(
    monkeypatch,
    failure_step,
    expected_status,
    expected_quality,
    expected_error_type,
    expected_error_fragment,
) -> None:
    symbol = f"OBS_{uuid4().hex[:10].upper()}"

    def ingest(received_symbol):
        assert received_symbol == symbol
        if failure_step == "ingest":
            raise RuntimeError("simulated provider failure")
        return 100

    def quality(received_symbol, results=None):
        assert received_symbol == symbol
        if failure_step == "quality":
            raise RuntimeError("simulated quality failure")
        return 4

    monkeypatch.setattr(runner, "_run_stock_pipeline", ingest)
    monkeypatch.setattr(runner, "_run_quality_checks", quality)
    monkeypatch.setattr(runner, "_build_marts", lambda: None)

    cfg = load_db_config()
    wait_for_db(cfg, timeout_s=10)

    try:
        metric = runner.run_orchestrated_pipeline(symbol=symbol)

        with connect(cfg) as conn:
            row = conn.execute(
                """
                SELECT status, quality_status, error_type, error_message, rows_processed
                FROM pipeline_runs
                WHERE pipeline_name = %s AND symbol = %s
                ORDER BY id DESC
                LIMIT 1
                """,
                ("market_data_lakehouse_pipeline", symbol),
            ).fetchone()

        assert row is not None
        assert metric.status == expected_status.lower()
        assert row[:3] == (expected_status, expected_quality, expected_error_type)
        if failure_step is None:
            assert row[3] is None
        else:
            assert expected_error_fragment in row[3]
        # Whatever the ingest step counts is what the stored run records. (That
        # the real ingest step counts rows received is covered by unit tests;
        # this stub stands in for it.)
        assert row[4] == (0 if failure_step == "ingest" else 100)
    finally:
        with connect(cfg) as conn:
            conn.execute("DELETE FROM pipeline_runs WHERE symbol = %s", (symbol,))
            conn.commit()
