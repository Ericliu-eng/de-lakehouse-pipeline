from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class CheckResult:
    check_name: str
    table_name: str
    passed: bool
    failed_rows: int
    details: str


def check_not_null(conn: Any, table_name: str, column_name: str) -> CheckResult:
    query = f"""
    SELECT COUNT(*) AS failed_rows
    FROM {table_name}
    WHERE {column_name} IS NULL
    """
    with conn.cursor() as cur:
        cur.execute(query)
        failed_rows = cur.fetchone()[0]

    return CheckResult(
        check_name="not_null",
        table_name=table_name,
        passed=failed_rows == 0,
        failed_rows=failed_rows,
        details=f"Column {column_name} has {failed_rows} NULL row(s).",
    )

def check_unique(conn: Any, table_name: str, column_name: str) -> CheckResult:
    query = f"""
    SELECT COUNT(*) FROM (
        SELECT {column_name}
        FROM {table_name}
        GROUP BY {column_name}
        HAVING COUNT(*) > 1
    ) AS duplicates
    """
    with conn.cursor() as cur:
        cur.execute(query)
        failed_rows = cur.fetchone()[0]

    return CheckResult(
        check_name="unique",
        table_name=table_name,
        passed=failed_rows == 0,
        failed_rows=failed_rows,
        details=f"Column {column_name} has {failed_rows} duplicated value group(s).",
    )