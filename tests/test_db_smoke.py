from __future__ import annotations

import os
# psycopg = Python ↔ Postgres bridge 
import psycopg
#import the pytest testing framework into your Python file
import pytest

from de_lakehouse_pipeline.db import load_db_config, wait_for_db, connect


def _table_exists(conn: psycopg.Connection, table_name: str) -> bool:
    with conn.cursor() as cur:
#PostgreSQL comes with (information_schema),The tables view contains information about all the tables.
        cur.execute(
            #""" 支持换行 要然很难阅读
            """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = %s
            )
            """,
            (table_name,),
#  错误写法 cur.execute(f"... table_name = '{table_name}'") ：SQL injection 风险
        )
        #return (True,) or  (False,) 
        row = cur.fetchone()
        exists = row[0]
        return bool(exists)


def _row_count(conn: psycopg.Connection, table_name: str) -> int:
    with conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM {table_name}")  # table_name is controlled below
    #data base return  EX:5 ,and then psycopg return [(5,)] tuple
        (n,) = cur.fetchone() #return a tuple so var = (n,)
        return int(n)

#pytest's "marker system"   only run pytest -m smoke , pytest -m "not smoke"
@pytest.mark.smoke
def test_db_smoke_connect_tables_seed() -> None:
    """
    Smoke test:
    - DB is reachable
    - expected tables exist (after migrate)
    - seed inserted (row count > 0)
    """
    cfg = load_db_config()

    # Fail fast if env is clearly wrong (helps debugging)
    assert cfg.host, "DB_HOST is empty"
    assert cfg.dbname, "DB_NAME is empty"
    assert cfg.user, "DB_USER is empty"

    wait_for_db(cfg, timeout_s=60)

    expected_table = os.environ.get("SMOKE_TABLE", "users")

    with connect(cfg) as conn:
        assert _table_exists(conn, expected_table), f"Expected table missing: {expected_table}"
        n = _row_count(conn, expected_table)
        assert n > 0, f"Expected seed data in {expected_table}, but row count is {n}"