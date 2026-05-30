import json

from de_lakehouse_pipeline.metrics import PipelineMetric, StepMetric, duration_seconds


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
