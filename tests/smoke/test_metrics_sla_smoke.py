from de_lakehouse_pipeline.metrics import SlaConfig, build_sla_report


def test_metrics_sla_smoke_report_can_be_built() -> None:
    report = build_sla_report(
        latest_data_at="2026-07-23T09:55:00+00:00",
        checked_at="2026-07-23T10:00:00+00:00",
        pipeline_started_at="2026-07-23T09:59:00+00:00",
        pipeline_finished_at="2026-07-23T10:00:00+00:00",
        failed_runs=0,
        total_runs=5,
        config=SlaConfig(
            max_freshness_minutes=30,
            max_latency_seconds=120,
            max_failure_rate=0.05,
        ),
    )

    payload = report.to_dict()

    assert payload["passed"] is True
    assert payload["data_freshness_minutes"] == 5
    assert payload["pipeline_latency_seconds"] == 60
    assert payload["failure_rate"] == 0.0