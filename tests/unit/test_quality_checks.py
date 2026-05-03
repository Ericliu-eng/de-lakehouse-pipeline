from de_lakehouse_pipeline.quality.checks import check_not_null, check_unique
from de_lakehouse_pipeline.quality.checks import check_range, check_freshness

class FakeCursor:
    def __init__(self, rows):
        self.rows = rows
        self.executed_query = ""

    def execute(self, query):
        self.executed_query = query

    def fetchone(self):
        return self.rows.pop(0)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

class FakeConn:
    def __init__(self, rows):
        self.rows = rows
        self.cursor_obj = FakeCursor(self.rows)

    def cursor(self):
        return self.cursor_obj
    

def test_check_not_null_passes_when_no_null_rows() -> None:
    conn = FakeConn([(0,)])
    result = check_not_null(conn, "stock_prices", "close")

    assert result.check_name == "not_null"
    assert result.passed is True
    assert result.failed_rows == 0
    assert "WHERE close IS NULL" in conn.cursor_obj.executed_query


def test_check_unique_passes_when_no_duplicates_exist() -> None:
    conn = FakeConn([(0,)])
    result = check_unique(conn, "stock_prices", "symbol")

    assert result.check_name == "unique"
    assert result.passed is True
    assert result.failed_rows == 0
    assert "HAVING COUNT(*) > 1" in conn.cursor_obj.executed_query

def test_check_range_passes_when_values_are_inside_range():
    conn = FakeConn([(0,)])

    result = check_range(
        conn,
        table_name="stock_prices",
        column_name="close_price",
        min_value=0,
    )

    assert result.check_name == "range"
    assert result.table_name == "stock_prices"
    assert result.passed is True
    assert result.failed_rows == 0

def test_check_range_fails_when_values_are_outside_range():
    conn = FakeConn([(2,)])

    result = check_range(
        conn,
        table_name="stock_prices",
        column_name="close_price",
        min_value=0,
    )

    assert result.check_name == "range"
    assert result.table_name == "stock_prices"
    assert result.passed is False
    assert result.failed_rows == 2



def test_check_freshness_passes_when_latest_data_is_recent():
    conn = FakeConn([(3,)])

    result = check_freshness(
        conn,
        table_name="stock_prices",
        timestamp_column="ts",
        max_age_days=14,
    )

    assert result.check_name == "freshness"
    assert result.table_name == "stock_prices"
    assert result.passed is True
    assert result.failed_rows == 0


def test_check_freshness_fails_when_latest_data_is_too_old():
    conn = FakeConn([(20,)])

    result = check_freshness(
        conn,
        table_name="stock_prices",
        timestamp_column="ts",
        max_age_days=14,
    )

    assert result.check_name == "freshness"
    assert result.table_name == "stock_prices"
    assert result.passed is False
    assert result.failed_rows == 1