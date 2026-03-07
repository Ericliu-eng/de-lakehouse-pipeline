from __future__ import annotations

import pytest
from de_lakehouse_pipeline.db import connect, load_db_config, wait_for_db
from de_lakehouse_pipeline.sql_utils import project_root, _read_sql, split_sql_statements




@pytest.mark.smoke
def test_window_query_runs() -> None:
    """Window function query file should execute without error."""
    root = project_root()
    sql_path = root / "sql" / "patterns_window.sql"
    sqls = _read_sql(sql_path)
    assert sqls, "patterns_window.sql is empty"

    cfg = load_db_config()
    wait_for_db(cfg, timeout_s=60)

    with connect(cfg) as conn:
        with conn.cursor() as cur:
            # Execute only the FIRST statement in the file (up to first ;)
            first_stmt = split_sql_statements(sqls)[0]
            cur.execute(first_stmt)
            rows = cur.fetchmany(5)
            assert rows is not None


@pytest.mark.smoke
def test_quality_checks_run() -> None:
    """Quality checks file should execute statement-by-statement without error."""
    root = project_root()
    sql_path = root / "sql" / "quality_checks.sql"
    sqls = _read_sql(sql_path)
    assert sqls, "quality_checks.sql is empty"

    cfg = load_db_config()
    wait_for_db(cfg, timeout_s=60)

    statements = split_sql_statements(sqls)

    with connect(cfg) as conn:
        with conn.cursor() as cur:
            for stmt in statements:
                cur.execute(stmt)
                _ = cur.fetchone()  # each check returns a single row