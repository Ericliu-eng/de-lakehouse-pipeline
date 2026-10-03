from contextlib import contextmanager
from pathlib import Path

from orchestration.dagster_pipeline import run_orchestrated_pipeline, run_step
from orchestration import dagster_pipeline as runner
import pytest
from uuid import uuid4

from de_lakehouse_pipeline.observability.run_repository import PipelineRunHandle
from de_lakehouse_pipeline.pipeline import StockLoadResult
from de_lakehouse_pipeline.quality.checks import CheckResult


def test_run_step_records_success() -> None:
    metric = run_step("example_success", lambda: 3)

    assert metric.step_name == "example_success"
    assert metric.status == "success"
    assert metric.row_count == 3
    assert metric.error_message is None
    assert metric.started_at
    assert metric.finished_at


def test_run_step_records_failure() -> None:
    def fail_step():
        raise RuntimeError("boom")

    metric = run_step("example_failure", fail_step)

    assert metric.step_name == "example_failure"
    assert metric.status == "failed"
    assert metric.row_count is None
    assert metric.error_type == "RuntimeError"
    assert metric.error_message == "boom"


def test_orchestrated_pipeline_stops_after_failed_step(monkeypatch, run_records) -> None:
    executed_steps = []

    def fake_run_step(step_name, fn):
        executed_steps.append(step_name)
        return original_run_step(step_name, fn)

    def fail_stock_pipeline(symbol):
        raise RuntimeError(f"failed for {symbol}")

    original_run_step = run_step

    monkeypatch.setattr(
        "orchestration.dagster_pipeline._run_stock_pipeline",
        fail_stock_pipeline,
    )
    monkeypatch.setattr(
        "orchestration.dagster_pipeline.run_step",
        fake_run_step,
    )

    metric = run_orchestrated_pipeline(symbol="TEST")

    assert metric.status == "failed"
    assert executed_steps == ["run_stock_pipeline"]
    assert len(metric.steps) == 1
    assert metric.steps[0].error_message == "failed for TEST"
    assert run_records[0] == ("start", "TEST")
    assert run_records[1][0] == "finish"
    assert run_records[1][1].status == "failed"


@pytest.mark.parametrize("failed_step", [0, 1, 2, None])
def test_cli_exit_status_and_downstream_steps(monkeypatch, capsys, failed_step, run_records):
    executed = []

    def step(index):
        def execute(*args):
            executed.append(index)
            if index == failed_step:
                raise RuntimeError("injected failure")
        return execute

    monkeypatch.setattr(runner, "configure_logging", lambda: None)
    monkeypatch.setattr("sys.argv", ["orchestrate", "--symbol", "AAPL"])
    for index, name in enumerate(["_run_stock_pipeline", "_run_quality_checks", "_build_marts"]):
        monkeypatch.setattr(runner, name, step(index))
    if failed_step is None:
        runner.main()
        assert executed == [0, 1, 2]
        assert "Status: success" in capsys.readouterr().out
    else:
        with pytest.raises(SystemExit) as exc:
            runner.main()
        assert exc.value.code == 1
        assert executed == list(range(failed_step + 1))
        assert "Status: failed" in capsys.readouterr().out


@pytest.fixture
def run_records(monkeypatch):
    recorded = []
    handle = PipelineRunHandle(
        id=73,
        external_run_id=uuid4(),
    )

    def start(metric, *, symbol):
        recorded.append(("start", symbol))
        return handle

    def finish(received_handle, metric):
        assert received_handle == handle
        recorded.append(("finish", metric))

    monkeypatch.setattr(runner, "_start_pipeline_run_record", start)
    monkeypatch.setattr(runner, "_finish_pipeline_run_record", finish)
    return recorded


def test_successful_pipeline_persists_success(monkeypatch, run_records) -> None:
    monkeypatch.setattr(runner, "_run_stock_pipeline", lambda symbol: None)
    monkeypatch.setattr(runner, "_run_quality_checks", lambda symbol, results=None: 4)
    monkeypatch.setattr(runner, "_build_marts", lambda: None)

    metric = run_orchestrated_pipeline(symbol="MSFT")

    assert metric.status == "success"
    assert run_records[0] == ("start", "MSFT")
    assert run_records[1] == ("finish", metric)


# --- reporting to PipeGuard ----------------------------------------------------


@pytest.fixture
def known_run(monkeypatch):
    """Record locally against a fixed handle, and capture what gets reported."""
    handle = PipelineRunHandle(id=91, external_run_id=uuid4())
    events = {"finished": [], "reports": []}

    monkeypatch.setattr(runner, "_start_pipeline_run_record", lambda metric, *, symbol: handle)
    monkeypatch.setattr(
        runner,
        "_finish_pipeline_run_record",
        lambda received, metric: events["finished"].append(metric),
    )
    monkeypatch.setattr(runner, "report_run", lambda report: events["reports"].append(report))
    events["handle"] = handle
    return events


def _check(name, passed=True, failed_rows=0):
    return CheckResult(name, "market_bars", passed, failed_rows, f"{name}: {failed_rows} row(s)")


def test_a_finished_run_is_reported_once_with_its_checks(monkeypatch, known_run) -> None:
    def quality(symbol, results):
        results.extend([_check("not_null"), _check("unique")])
        return 2

    monkeypatch.setattr(runner, "_run_stock_pipeline", lambda symbol: 100)
    monkeypatch.setattr(runner, "_run_quality_checks", quality)
    monkeypatch.setattr(runner, "_build_marts", lambda: None)

    run_orchestrated_pipeline(symbol="AAPL")

    assert len(known_run["reports"]) == 1
    report = known_run["reports"][0]
    # The same UUID as the local record, so PipeGuard treats a resend as a retry.
    assert report["external_run_id"] == str(known_run["handle"].external_run_id)
    assert report["status"] == "SUCCESS"
    assert report["rows_processed"] == 100
    assert [check["check_name"] for check in report["checks"]] == ["not_null", "unique"]


def test_a_run_that_stops_on_bad_data_still_reports_the_failing_checks(
    monkeypatch, known_run
) -> None:
    def quality(symbol, results):
        results.extend([_check("not_null"), _check("unique", passed=False, failed_rows=3)])
        raise RuntimeError("Quality checks failed: unique")

    monkeypatch.setattr(runner, "_run_stock_pipeline", lambda symbol: 100)
    monkeypatch.setattr(runner, "_run_quality_checks", quality)

    metric = run_orchestrated_pipeline(symbol="AAPL")

    assert metric.status == "failed"
    report = known_run["reports"][0]
    assert report["status"] == "FAILED"
    assert report["error_message"] == "Quality checks failed: unique"
    assert {check["check_name"]: check["status"] for check in report["checks"]} == {
        "not_null": "PASS",
        "unique": "FAIL",
    }


def test_a_reporting_failure_never_changes_the_outcome_of_a_run(monkeypatch, known_run) -> None:
    def broken_report(report):
        raise RuntimeError("bug in reporting")

    monkeypatch.setattr(runner, "report_run", broken_report)
    monkeypatch.setattr(runner, "_run_stock_pipeline", lambda symbol: 100)
    monkeypatch.setattr(runner, "_run_quality_checks", lambda symbol, results: 0)
    monkeypatch.setattr(runner, "_build_marts", lambda: None)

    metric = run_orchestrated_pipeline(symbol="AAPL")

    assert metric.status == "success"
    # The local record is written before reporting is even attempted.
    assert known_run["finished"] == [metric]


def test_the_ingest_step_counts_rows_received_not_rows_loaded(monkeypatch) -> None:
    result = StockLoadResult(raw_path=Path("raw.json"), rows_received=100, rows_loaded=1)
    monkeypatch.setattr(runner, "load_stock", lambda symbol: result)

    assert runner._run_stock_pipeline("AAPL") == 100


def test_quality_results_are_kept_even_when_the_checks_fail(monkeypatch) -> None:
    @contextmanager
    def fake_connect(cfg):
        yield object()

    monkeypatch.setattr(runner, "load_db_config", lambda: object())
    monkeypatch.setattr(runner, "wait_for_db", lambda cfg, timeout_s: None)
    monkeypatch.setattr(runner, "connect", fake_connect)
    monkeypatch.setattr(
        runner,
        "run_stock_quality_checks",
        lambda conn, symbol: [_check("not_null"), _check("unique", passed=False, failed_rows=2)],
    )
    collected = []

    with pytest.raises(RuntimeError):
        runner._run_quality_checks("AAPL", collected)

    assert [check.check_name for check in collected] == ["not_null", "unique"]
