from __future__ import annotations

from pathlib import Path

import pytest

from de_lakehouse_pipeline.db import connect, load_db_config, wait_for_db


def _read_sql(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


@pytest.mark.smoke
def test_window_query_runs() -> None:
    """Window function query file should execute without error."""
    root = Path(__file__).resolve().parents[1]
    sql_path = root / "sql" / "patterns_window.sql"
    sql = _read_sql(sql_path)
    assert sql, "patterns_window.sql is empty"

    cfg = load_db_config()
    wait_for_db(cfg, timeout_s=60)

    with connect(cfg) as conn:
        with conn.cursor() as cur:
            # Execute only the FIRST statement in the file (up to first ;)
            first_stmt = sql.split(";")[0].strip()
            cur.execute(first_stmt)
            rows = cur.fetchmany(5)
            assert rows is not None


@pytest.mark.smoke
def test_quality_checks_run() -> None:
    """Quality checks file should execute statement-by-statement without error."""
    root = Path(__file__).resolve().parents[1]
    sql_path = root / "sql" / "quality_checks.sql"
    sql = _read_sql(sql_path)
    assert sql, "quality_checks.sql is empty"

    cfg = load_db_config()
    wait_for_db(cfg, timeout_s=60)

    statements = [s.strip() for s in sql.split(";") if s.strip()]

    with connect(cfg) as conn:
        with conn.cursor() as cur:
            for stmt in statements:
                cur.execute(stmt)
                _ = cur.fetchone()  # each check returns a single row