import json

from de_lakehouse_pipeline.metrics import (
    PipelineMetric,
    SlaConfig,
    StepMetric,
    build_sla_report,
    classify_failure,
    duration_seconds,
    failure_rate,
    freshness_minutes,
)


def test_duration_seconds_from_iso_timestamps() -> None:
    assert duration_seconds(
        "2026-05-30T10:00:00+00:00",
        "2026-05-30T10:00:01.250000+00:00",
    ) == 1.25


def test_pipeline_metric_serializes_steps_and_duration() -> None:
    metric = PipelineMetric(
        pipeline_name="market_data_lakehouse_pipeline",
        started_at="2026-05-30T10:00:00+00:00",
        finished_at="2026-05-30T10:00:03+00:00",
        status="success",
    )
    metric.add_step(
        StepMetric(
            step_name="build_marts",
            status="success",
            started_at="2026-05-30T10:00:01+00:00",
            finished_at="2026-05-30T10:00:02+00:00",
            row_count=3,
        )
    )

    payload = metric.to_dict()

    assert payload["pipeline_name"] == "market_data_lakehouse_pipeline"
    assert payload["duration_seconds"] == 3
    assert payload["steps"][0]["step_name"] == "build_marts"
    assert payload["steps"][0]["duration_seconds"] == 1
    assert json.loads(metric.to_json()) == payload


def test_freshness_minutes_returns_minutes_since_latest_data() -> None:
    assert freshness_minutes(
        "2026-07-21T09:45:00+00:00",
        "2026-07-21T10:00:00+00:00",
    ) == 15


def test_failure_rate_returns_failed_runs_divided_by_total_runs() -> None:
    assert failure_rate(failed_runs=2, total_runs=10) == 0.2
    assert failure_rate(failed_runs=2, total_runs=0) == 0.0

def test_build_sla_report_passes_when_metrics_are_within_thresholds() -> None:
    report = build_sla_report(
        latest_data_at="2026-07-21T09:50:00+00:00",
        checked_at="2026-07-21T10:00:00+00:00",
        pipeline_started_at="2026-07-21T09:59:00+00:00",
        pipeline_finished_at="2026-07-21T10:00:00+00:00",
        failed_runs=1,
        total_runs=100,
        config=SlaConfig(
            max_freshness_minutes=30,
            max_latency_seconds=120,
            max_failure_rate=0.05,
        ),
    )

    assert report.passed is True
    assert report.violations == []
    assert report.data_freshness_minutes == 10
    assert report.pipeline_latency_seconds == 60
    assert report.failure_rate == 0.01

def test_build_sla_report_flags_freshness_latency_and_failure_rate_breaches() -> None:
    report = build_sla_report(
        latest_data_at="2026-07-21T08:00:00+00:00",
        checked_at="2026-07-21T10:00:00+00:00",
        pipeline_started_at="2026-07-21T09:00:00+00:00",
        pipeline_finished_at="2026-07-21T10:00:00+00:00",
        failed_runs=10,
        total_runs=100,
        config=SlaConfig(
            max_freshness_minutes=30,
            max_latency_seconds=300,
            max_failure_rate=0.05,
        ),
    )

    assert report.passed is False
    assert report.violations == [
        "freshness_sla_breached",
        "latency_sla_breached",
        "failure_rate_sla_breached",
    ]

def test_classify_failure_returns_retryable_non_retryable_or_unknown() -> None:
    assert classify_failure("timeout") == "retryable"
    assert classify_failure("schema") == "non_retryable"
    assert classify_failure("unexpected") == "unknown"
#edge test
def test_build_sla_report_flags_missing_freshness_and_latency() -> None:
    report = build_sla_report(
        latest_data_at=None,
        checked_at="2026-07-21T10:00:00+00:00",
        pipeline_started_at="2026-07-21T09:59:00+00:00",
        pipeline_finished_at=None,
        failed_runs=0,
        total_runs=10,
        config=SlaConfig(),
    )

    assert report.passed is False
    assert report.violations == ["freshness_missing", "latency_missing"]
    assert report.data_freshness_minutes is None
    assert report.pipeline_latency_seconds is None