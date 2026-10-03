from uuid import uuid4

import pytest
import requests

from de_lakehouse_pipeline.metrics import PipelineMetric, StepMetric
from de_lakehouse_pipeline.observability.pipeguard_reporter import (
    PipeGuardConfig,
    build_run_report,
    load_pipeguard_config,
    report_run,
)
from de_lakehouse_pipeline.quality.checks import CheckResult

CONFIG = PipeGuardConfig(url="https://pipeguard.example", api_key="secret", timeout_seconds=2.0)
STARTED = "2026-10-02T12:00:00+00:00"
FINISHED = "2026-10-02T12:00:04+00:00"


def _step(name: str, status: str = "success", **fields) -> StepMetric:
    return StepMetric(
        step_name=name,
        status=status,
        started_at=STARTED,
        finished_at=FINISHED,
        **fields,
    )


def _metric(status: str = "success", steps: list[StepMetric] | None = None) -> PipelineMetric:
    return PipelineMetric(
        pipeline_name="market_data_lakehouse_pipeline",
        started_at=STARTED,
        finished_at=FINISHED,
        status=status,
        steps=steps or [_step("run_stock_pipeline", row_count=100)],
    )


def _check(name: str, passed: bool = True, failed_rows: int = 0) -> CheckResult:
    return CheckResult(
        check_name=name,
        table_name="market_bars",
        passed=passed,
        failed_rows=failed_rows,
        details=f"{name} on market_bars: {failed_rows} failing row(s)",
    )


class FakeResponse:
    def __init__(self, status_code: int, text: str = "") -> None:
        self.status_code = status_code
        self.text = text


class FakeSession:
    def __init__(self, response: FakeResponse | None = None, error: Exception | None = None):
        self.response = response
        self.error = error
        self.calls: list[tuple[str, dict]] = []

    def post(self, url: str, **kwargs):
        self.calls.append((url, kwargs))
        if self.error is not None:
            raise self.error
        return self.response


# --- configuration -------------------------------------------------------------


@pytest.mark.parametrize(
    "env",
    [
        {},
        {"PIPEGUARD_API_URL": "https://pipeguard.example"},
        {"PIPEGUARD_API_KEY": "secret"},
        {"PIPEGUARD_API_URL": "  ", "PIPEGUARD_API_KEY": "secret"},
    ],
)
def test_reporting_stays_off_unless_both_url_and_key_are_set(env) -> None:
    assert load_pipeguard_config(env) is None


def test_config_drops_a_trailing_slash_and_keeps_a_valid_timeout() -> None:
    config = load_pipeguard_config(
        {
            "PIPEGUARD_API_URL": "https://pipeguard.example/",
            "PIPEGUARD_API_KEY": "secret",
            "PIPEGUARD_TIMEOUT_SECONDS": "3.5",
        }
    )

    assert config == PipeGuardConfig("https://pipeguard.example", "secret", 3.5)


def test_an_unparseable_timeout_falls_back_to_the_default() -> None:
    config = load_pipeguard_config(
        {
            "PIPEGUARD_API_URL": "https://pipeguard.example",
            "PIPEGUARD_API_KEY": "secret",
            "PIPEGUARD_TIMEOUT_SECONDS": "soon",
        }
    )

    assert config is not None
    assert config.timeout_seconds == 5.0


# --- payload -------------------------------------------------------------------


def test_a_successful_run_maps_onto_the_report_contract() -> None:
    run_id = uuid4()

    report = build_run_report(
        metric=_metric(),
        external_run_id=run_id,
        rows_processed=100,
        checks=[_check("not_null")],
    )

    assert report == {
        "pipeline_name": "market_data_lakehouse_pipeline",
        "external_run_id": str(run_id),
        "status": "SUCCESS",
        "started_at": STARTED,
        "finished_at": FINISHED,
        "rows_processed": 100,
        "error_type": None,
        "error_message": None,
        "checks": [
            {
                "check_name": "not_null",
                "status": "PASS",
                "metric_value": 0.0,
                "threshold": 0.0,
                "message": "not_null on market_bars: 0 failing row(s)",
            }
        ],
    }


def test_a_failed_run_carries_the_error_of_the_step_that_failed() -> None:
    metric = _metric(
        status="failed",
        steps=[
            _step("run_stock_pipeline", row_count=100),
            _step(
                "run_quality_checks",
                status="failed",
                error_type="RuntimeError",
                error_message="Quality checks failed: unique",
            ),
        ],
    )

    report = build_run_report(
        metric=metric,
        external_run_id=uuid4(),
        rows_processed=100,
        checks=[_check("unique", passed=False, failed_rows=3)],
    )

    assert report["status"] == "FAILED"
    assert report["error_type"] == "RuntimeError"
    assert report["error_message"] == "Quality checks failed: unique"
    # A failed check reports how many rows broke it, against a threshold of zero.
    assert report["checks"][0]["status"] == "FAIL"
    assert report["checks"][0]["metric_value"] == 3.0
    assert report["checks"][0]["threshold"] == 0.0


def test_a_check_without_details_still_gets_a_message() -> None:
    check = CheckResult("range", "market_bars", passed=True, failed_rows=0, details="")

    report = build_run_report(
        metric=_metric(), external_run_id=uuid4(), rows_processed=1, checks=[check]
    )

    assert report["checks"][0]["message"] == "range on market_bars"


def test_an_unfinished_run_cannot_be_reported() -> None:
    metric = _metric()
    metric.finished_at = None

    with pytest.raises(ValueError):
        build_run_report(metric=metric, external_run_id=uuid4(), rows_processed=0)


# --- sending -------------------------------------------------------------------


def test_a_report_is_posted_with_the_key_and_a_bounded_timeout() -> None:
    session = FakeSession(FakeResponse(201))
    report = {"external_run_id": "abc"}

    assert report_run(report, CONFIG, session=session) is True

    url, kwargs = session.calls[0]
    assert url == "https://pipeguard.example/runs"
    assert kwargs["json"] == report
    assert kwargs["headers"] == {"X-API-Key": "secret"}
    # Bounded so a sleeping monitor can delay a run by seconds, not indefinitely.
    assert kwargs["timeout"] == 2.0


def test_a_retry_that_pipeguard_already_has_counts_as_reported() -> None:
    assert report_run({}, CONFIG, session=FakeSession(FakeResponse(200))) is True


@pytest.mark.parametrize("status_code", [401, 409, 422, 500, 503])
def test_a_rejected_report_is_logged_and_dropped(status_code, caplog) -> None:
    session = FakeSession(FakeResponse(status_code, text="nope"))

    assert report_run({"external_run_id": "abc"}, CONFIG, session=session) is False
    assert f"HTTP {status_code}" in caplog.text


@pytest.mark.parametrize(
    "error",
    [requests.Timeout("read timed out"), requests.ConnectionError("refused")],
)
def test_an_unreachable_pipeguard_never_raises_into_the_pipeline(error, caplog) -> None:
    session = FakeSession(error=error)

    assert report_run({"external_run_id": "abc"}, CONFIG, session=session) is False
    assert "was not reported" in caplog.text


def test_nothing_is_sent_when_reporting_is_not_configured() -> None:
    session = FakeSession(FakeResponse(201))

    # The autouse fixture clears the PIPEGUARD_* variables, so this reads none.
    assert report_run({"external_run_id": "abc"}, session=session) is False
    assert session.calls == []
