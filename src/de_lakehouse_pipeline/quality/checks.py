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

def check_range(
    conn: Any,
    table_name: str,
    column_name: str,
    min_value: float | None = None,
    max_value: float | None = None,
) -> CheckResult:
    conditions = []

    if min_value is not None:
        conditions.append(f"{column_name} < {min_value}")

    if max_value is not None:
        conditions.append(f"{column_name} > {max_value}")

    if not conditions:
        raise ValueError("At least one of min_value or max_value must be provided.")

    where_clause = " OR ".join(conditions)

    query = f"""
    SELECT COUNT(*) AS failed_rows
    FROM {table_name}
    WHERE {where_clause}
    """

    with conn.cursor() as cur:
        cur.execute(query)
        failed_rows = cur.fetchone()[0]

    return CheckResult(
        check_name="range",
        table_name=table_name,
        passed=failed_rows == 0,
        failed_rows=failed_rows,
        details=(
            f"Column {column_name} has {failed_rows} row(s) outside "
            f"range min={min_value}, max={max_value}."
        ),
    )
def check_freshness(
    conn: Any,
    table_name: str,
    timestamp_column: str,
    max_age_days: int,
) -> CheckResult:
    query = f"""
    SELECT
        CASE
            WHEN MAX({timestamp_column}) IS NULL THEN NULL
            ELSE CURRENT_DATE - MAX({timestamp_column})::date
        END AS age_days
    FROM {table_name}
    """

    with conn.cursor() as cur:
        cur.execute(query)
        age_days = cur.fetchone()[0]

    if age_days is None:
        return CheckResult(
            check_name="freshness",
            table_name=table_name,
            passed=False,
            failed_rows=1,
            details=f"Table {table_name} has no timestamp data in {timestamp_column}.",
        )

    failed_rows = 0 if age_days <= max_age_days else 1

    return CheckResult(
        check_name="freshness",
        table_name=table_name,
        passed=failed_rows == 0,
        failed_rows=failed_rows,
        details=(
            f"Latest {timestamp_column} is {age_days} day(s) old; "
            f"max allowed age is {max_age_days} day(s)."
        ),
    )

def run_stock_quality_checks(conn: Any) -> list[CheckResult]:
    return [
        check_not_null(conn, "stock_prices", "symbol"),
        check_not_null(conn, "stock_prices", "ts"),
        check_unique(conn, "stock_prices", "symbol, ts"),
        check_range(conn, "stock_prices", "close_price", min_value=0),
        check_range(conn, "stock_prices", "volume", min_value=0),
        check_freshness(conn, "stock_prices", "ts", max_age_days=14),
    ]