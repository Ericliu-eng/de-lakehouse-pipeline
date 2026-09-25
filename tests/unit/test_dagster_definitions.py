import pytest

from de_lakehouse_pipeline.quality.checks import CheckResult
from orchestration import definitions


class FakeConnection:
    def __init__(self, events):
        self.events = events

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def commit(self):
        self.events.append("commit")


def check(passed: bool) -> CheckResult:
    return CheckResult(
        check_name="range",
        table_name="market_bars",
        passed=passed,
        failed_rows=0 if passed else 1,
        details="ok" if passed else "Column close has 1 row(s) outside range",
    )


@pytest.fixture
def events(monkeypatch):
    recorded = []
    monkeypatch.setattr(definitions, "run_stock", lambda symbol: recorded.append(("ingest", symbol)))
    monkeypatch.setattr(definitions, "load_db_config", lambda: "cfg")
    monkeypatch.setattr(definitions, "wait_for_db", lambda cfg, timeout_s: None)
    monkeypatch.setattr(definitions, "connect", lambda cfg: FakeConnection(recorded))
    for name in ["run_daily_summary", "run_latest_price", "run_symbol_volume"]:
        monkeypatch.setattr(definitions, name, lambda conn, name=name: recorded.append(name))
    return recorded


def set_quality_results(monkeypatch, events, results):
    def fake_checks(conn, symbol):
        events.append(("quality", symbol))
        return results

    monkeypatch.setattr(definitions, "run_stock_quality_checks", fake_checks)


def run_job(symbol=None):
    run_config = {"ops": {"ingest_stock": {"config": {"symbol": symbol}}}} if symbol else None
    return definitions.stock_lakehouse_job.execute_in_process(run_config=run_config, raise_on_error=False)


def test_job_runs_ingest_quality_and_marts_in_order(monkeypatch, events):
    set_quality_results(monkeypatch, events, [check(True), check(True)])

    result = run_job("MSFT")

    assert result.success
    assert events == [
        ("ingest", "MSFT"),
        ("quality", "MSFT"),
        "run_daily_summary",
        "run_latest_price",
        "run_symbol_volume",
        "commit",
    ]


def test_job_defaults_to_aapl(monkeypatch, events):
    set_quality_results(monkeypatch, events, [check(True)])

    result = run_job()

    assert result.success
    assert events[0] == ("ingest", "AAPL")


def test_quality_failure_stops_marts(monkeypatch, events):
    set_quality_results(monkeypatch, events, [check(True), check(False)])

    result = run_job("MSFT")

    assert not result.success
    assert events == [("ingest", "MSFT"), ("quality", "MSFT")]
    failure = result.failure_data_for_node("run_quality_checks")
    assert "Column close has 1 row(s) outside range" in failure.error.cause.message


def test_ingest_failure_skips_downstream_ops(monkeypatch, events):
    def fail_ingest(symbol):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(definitions, "run_stock", fail_ingest)
    set_quality_results(monkeypatch, events, [check(True)])

    result = run_job("MSFT")

    assert not result.success
    assert events == []


def test_definitions_register_job_and_daily_schedule():
    schedule = definitions.daily_stock_lakehouse_schedule

    assert list(definitions.defs.jobs) == [definitions.stock_lakehouse_job]
    assert list(definitions.defs.schedules) == [schedule]
    assert schedule.cron_schedule == "0 8 * * *"
    assert schedule.job_name == "stock_lakehouse_job"
