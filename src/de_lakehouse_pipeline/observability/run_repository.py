from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from psycopg import Connection


RUNNING = "RUNNING"
TERMINAL_STATUSES = {"SUCCESS", "FAILED"}
QUALITY_STATUSES = {"NOT_EVALUATED", "PASS", "WARN", "FAIL"}


@dataclass(frozen=True)
class PipelineRunHandle:
    """Database identity returned when a pipeline run starts."""

    id: int
    external_run_id: UUID


def start_pipeline_run(
    conn: Connection,
    *,
    pipeline_name: str,
    started_at: datetime,
    source: str | None = None,
    symbol: str | None = None,
    external_run_id: UUID | None = None,
) -> PipelineRunHandle:
    """Insert a RUNNING record in the caller's transaction."""
    normalized_name = pipeline_name.strip()
    if not normalized_name:
        raise ValueError("pipeline_name must not be empty")

    run_uuid = external_run_id or uuid4()
    sql = """
    INSERT INTO pipeline_runs (
        pipeline_name,
        external_run_id,
        source,
        symbol,
        status,
        started_at
    )
    VALUES (%s, %s, %s, %s, %s, %s)
    RETURNING id
    """

    with conn.cursor() as cur:
        cur.execute(
            sql,
            (
                normalized_name,
                run_uuid,
                _clean_optional_text(source),
                _clean_optional_text(symbol),
                RUNNING,
                started_at,
            ),
        )
        row = cur.fetchone()

    if row is None:
        raise RuntimeError("pipeline run insert did not return an id")

    return PipelineRunHandle(id=int(row[0]), external_run_id=run_uuid)


def finish_pipeline_run(
    conn: Connection,
    *,
    run_id: int,
    status: str,
    finished_at: datetime,
    quality_status: str = "NOT_EVALUATED",
    rows_processed: int = 0,
    error_type: str | None = None,
    error_message: str | None = None,
) -> None:
    """Finalize a pipeline run in the caller's transaction."""
    normalized_status = status.strip().upper()
    if normalized_status not in TERMINAL_STATUSES:
        allowed = ", ".join(sorted(TERMINAL_STATUSES))
        raise ValueError(f"status must be one of: {allowed}")

    normalized_quality_status = quality_status.strip().upper()
    if normalized_quality_status not in QUALITY_STATUSES:
        allowed = ", ".join(sorted(QUALITY_STATUSES))
        raise ValueError(f"quality_status must be one of: {allowed}")

    if rows_processed < 0:
        raise ValueError("rows_processed must be non-negative")

    sql = """
    UPDATE pipeline_runs
    SET status = %s,
        quality_status = %s,
        finished_at = %s,
        duration_ms = GREATEST(
            0,
            ROUND(EXTRACT(EPOCH FROM (%s - started_at)) * 1000)::BIGINT
        ),
        rows_processed = %s,
        error_type = %s,
        error_message = %s
    WHERE id = %s
    RETURNING id
    """

    with conn.cursor() as cur:
        cur.execute(
            sql,
            (
                normalized_status,
                normalized_quality_status,
                finished_at,
                finished_at,
                rows_processed,
                _clean_optional_text(error_type),
                _clean_optional_text(error_message),
                run_id,
            ),
        )
        row = cur.fetchone()

    if row is None:
        raise LookupError(f"pipeline run {run_id} does not exist")


def _clean_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None
