from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from de_lakehouse_pipeline.load.db.connection import connect, load_db_config
from de_lakehouse_pipeline.load.db.pipeline_metadata import (
    get_last_watermark,
    upsert_watermark,
)


@pytest.fixture
def db_conn():
    cfg = load_db_config()
    conn = connect(cfg)
    try:
        yield conn
    finally:
        conn.rollback()
        conn.close()


def test_get_last_watermark_returns_none_when_missing(db_conn):
    source = "metadata_test"
    symbol = "MISSING"

    _clean_metadata(db_conn, source, symbol)

    result = get_last_watermark(db_conn, source, symbol)

    assert result is None


def test_upsert_watermark_inserts_new_row(db_conn):
    source = "metadata_test"
    symbol = "INSERT"
    watermark = datetime(2026, 4, 15, 10, 0, tzinfo=ZoneInfo("UTC"))

    _clean_metadata(db_conn, source, symbol)

    upsert_watermark(
        db_conn,
        source,
        symbol,
        last_watermark=watermark,
        last_row_count=3,
        status="success",
    )

    with db_conn.cursor() as cur:
        cur.execute(
            """
            SELECT last_watermark, last_row_count, status
            FROM pipeline_metadata
            WHERE source = %s AND symbol = %s
            """,
            (source, symbol),
        )
        row = cur.fetchone()

    assert row is not None
    assert row[0] == watermark
    assert row[1] == 3
    assert row[2] == "success"

    _clean_metadata(db_conn, source, symbol)


def test_upsert_watermark_updates_existing_row(db_conn):
    source = "metadata_test"
    symbol = "UPDATE"
    first_watermark = datetime(2026, 4, 14, 10, 0, tzinfo=ZoneInfo("UTC"))
    second_watermark = datetime(2026, 4, 15, 10, 0, tzinfo=ZoneInfo("UTC"))

    _clean_metadata(db_conn, source, symbol)

    upsert_watermark(
        db_conn,
        source,
        symbol,
        last_watermark=first_watermark,
        last_row_count=2,
        status="success",
    )

    upsert_watermark(
        db_conn,
        source,
        symbol,
        last_watermark=second_watermark,
        last_row_count=5,
        status="success",
    )

    with db_conn.cursor() as cur:
        cur.execute(
            """
            SELECT last_watermark, last_row_count, status
            FROM pipeline_metadata
            WHERE source = %s AND symbol = %s
            """,
            (source, symbol),
        )
        row = cur.fetchone()

    assert row is not None
    assert row[0] == second_watermark
    assert row[1] == 5
    assert row[2] == "success"

    _clean_metadata(db_conn, source, symbol)


def _clean_metadata(conn, source: str, symbol: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            DELETE FROM pipeline_metadata
            WHERE source = %s AND symbol = %s
            """,
            (source, symbol),
        )
    conn.commit()
