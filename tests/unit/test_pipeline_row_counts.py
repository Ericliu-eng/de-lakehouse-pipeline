from contextlib import contextmanager

from de_lakehouse_pipeline import pipeline


def _bar(close: str) -> dict:
    return {
        "1. open": close,
        "2. high": close,
        "3. low": close,
        "4. close": close,
        "5. volume": "1000",
    }


PAYLOAD = {
    "Meta Data": {"2. Symbol": "AAPL", "5. Time Zone": "UTC"},
    "Time Series (Daily)": {
        "2026-09-16": _bar("100.0"),
        "2026-09-17": _bar("101.0"),
        "2026-09-18": _bar("102.0"),
    },
}


def _staged_timestamps() -> list:
    # Taken from the real staging code rather than written by hand, so the test
    # does not have to guess how dates are normalised to the warehouse grain.
    rows = pipeline.staged_rows_to_db_tuples(pipeline.stage_alpha_vantage_daily(PAYLOAD))
    return sorted(row[0] for row in rows)


def _stub_source_and_database(monkeypatch, *, payload, last_watermark) -> dict:
    written: dict = {}

    @contextmanager
    def fake_connect(cfg):
        yield object()

    monkeypatch.setenv("ENABLE_S3_RAW_UPLOAD", "false")
    monkeypatch.setattr(pipeline, "fetch_daily_stock", lambda symbol: payload)
    monkeypatch.setattr(pipeline, "load_db_config", lambda: object())
    monkeypatch.setattr(pipeline, "wait_for_db", lambda cfg, timeout_s: None)
    monkeypatch.setattr(pipeline, "connect", fake_connect)
    monkeypatch.setattr(pipeline, "get_last_watermark", lambda conn, source, symbol: last_watermark)
    monkeypatch.setattr(
        pipeline,
        "upsert_stock_prices",
        lambda conn, rows: written.setdefault("rows", list(rows)),
    )
    monkeypatch.setattr(pipeline, "upsert_watermark", lambda *args, **kwargs: None)
    monkeypatch.setattr(pipeline, "insert_load_metadata", lambda *args, **kwargs: None)
    return written


def test_received_and_loaded_rows_are_counted_separately(monkeypatch, tmp_path) -> None:
    # The watermark already covers two of the three days, as it does on a normal
    # incremental run: the source sends the whole window, one row is new.
    second_latest = _staged_timestamps()[-2]
    written = _stub_source_and_database(monkeypatch, payload=PAYLOAD, last_watermark=second_latest)

    result = pipeline.load_stock(symbol="AAPL", root=tmp_path)

    assert result.rows_received == 3
    assert result.rows_loaded == 1
    assert len(written["rows"]) == 1


def test_an_up_to_date_warehouse_loads_nothing_but_still_received_rows(
    monkeypatch, tmp_path
) -> None:
    # This is every weekend run: nothing new to load, yet the source answered in
    # full. A row-count monitor has to watch the second number, not the first.
    latest = _staged_timestamps()[-1]
    written = _stub_source_and_database(monkeypatch, payload=PAYLOAD, last_watermark=latest)

    result = pipeline.load_stock(symbol="AAPL", root=tmp_path)

    assert result.rows_received == 3
    assert result.rows_loaded == 0
    assert "rows" not in written


def test_an_empty_payload_received_nothing(monkeypatch, tmp_path) -> None:
    empty = {"Meta Data": PAYLOAD["Meta Data"], "Time Series (Daily)": {}}
    _stub_source_and_database(monkeypatch, payload=empty, last_watermark=None)

    result = pipeline.load_stock(symbol="AAPL", root=tmp_path)

    assert (result.rows_received, result.rows_loaded) == (0, 0)


def test_run_stock_still_returns_the_raw_payload_path(monkeypatch, tmp_path) -> None:
    _stub_source_and_database(monkeypatch, payload=PAYLOAD, last_watermark=None)

    # Callers across the CLI, Dagster, scripts and tests use this return value.
    path = pipeline.run_stock(symbol="AAPL", root=tmp_path)

    assert path.exists()
    assert tmp_path in path.parents
