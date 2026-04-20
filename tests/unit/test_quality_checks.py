from de_lakehouse_pipeline.quality.checks import check_not_null, check_unique


class FakeCursor:
    def __init__(self, fetchone_result):
        self.fetchone_result = fetchone_result
        self.executed_query = None

    def execute(self, query):
        self.executed_query = query

    def fetchone(self):
        return self.fetchone_result

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return None


class FakeConnection:
    def __init__(self, fetchone_result):
        self.cursor_obj = FakeCursor(fetchone_result)

    def cursor(self):
        return self.cursor_obj


def test_check_not_null_passes_when_no_null_rows() -> None:
    conn = FakeConnection((0,))
    result = check_not_null(conn, "stock_prices", "close")

    assert result.check_name == "not_null"
    assert result.passed is True
    assert result.failed_rows == 0
    assert "WHERE close IS NULL" in conn.cursor_obj.executed_query


def test_check_unique_passes_when_no_duplicates_exist() -> None:
    conn = FakeConnection((0,))
    result = check_unique(conn, "stock_prices", "symbol")

    assert result.check_name == "unique"
    assert result.passed is True
    assert result.failed_rows == 0
    assert "HAVING COUNT(*) > 1" in conn.cursor_obj.executed_query