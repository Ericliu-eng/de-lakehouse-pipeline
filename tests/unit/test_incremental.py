# test_filter_new_rows_when_none
# test_filter_new_rows_partial
# test_filter_new_rows_empty
# test_get_max_timestamp_empty  # e
from de_lakehouse_pipeline.transform.incremental import get_max_timestamp,filter_new_rows

def test_filter_new_rows_when_watermark_is_none():
    test_rows = [
    (1, "mon"),
    (2, "tues"),
    (3, "wes"),
]
    last_watermark = None
    after_filter = filter_new_rows(test_rows,last_watermark)
    assert after_filter == test_rows

def test_filter_new_rows_only_keeps_newer_rows():
    test_rows = [
    (1, "mon"),
    (2, "tues"),
    (3, "wes"),
]
    last_watermark = 2
    new_rows = filter_new_rows(test_rows,last_watermark)
    assert new_rows == [(3, "wes")]


def test_filter_new_rows_returns_empty_when_no_new_data():
    test_rows = [
    (1, "mon"),
    (2, "tues"),
    (3, "wes"),
]
    last_watermark = 3
    new_rows = filter_new_rows(test_rows,last_watermark)
    assert new_rows == []    

def test_get_max_timestamp_empty():
    test_rows = []
    result = get_max_timestamp(test_rows)
    assert result is None