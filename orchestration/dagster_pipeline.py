from __future__ import annotations

from de_lakehouse_pipeline.metrics import PipelineMetric, StepMetric, utc_now


def run_step(step_name: str, row_count: int | None = None) -> StepMetric:
    started_at = utc_now()

    try:
        print(f"Running step: {step_name}")

        # Placeholder for the real pipeline step.
        # Later this can call ingest, load, transform, quality checks, marts,
        # and metadata tracking.

        status = "success"
        error_message = None

    except Exception as exc:
        status = "failed"
        error_message = str(exc)
        print(f"Step failed: {step_name}")
        print(f"Error: {error_message}")

    finished_at = utc_now()

    return StepMetric(
        step_name=step_name,
        status=status,
        started_at=started_at,
        finished_at=finished_at,
        row_count=row_count,
        error_message=error_message,
    )


def run_orchestrated_pipeline() -> PipelineMetric:
    pipeline_metric = PipelineMetric(
        pipeline_name="market_data_lakehouse_pipeline",
        started_at=utc_now(),
    )

    steps = [
        "ingest_raw_stock_data",
        "load_raw_data_to_database",
        "run_transformations",
        "run_quality_checks",
        "build_marts",
        "record_pipeline_metadata",
    ]

    for step in steps:
        step_metric = run_step(step)
        pipeline_metric.add_step(step_metric)

    failed_steps = [
        step for step in pipeline_metric.steps if step.status == "failed"
    ]

    final_status = "failed" if failed_steps else "success"
    pipeline_metric.finish(status=final_status)

    return pipeline_metric


if __name__ == "__main__":
    metric = run_orchestrated_pipeline()

    print("\nPipeline run summary:")
    print(f"Pipeline: {metric.pipeline_name}")
    print(f"Status: {metric.status}")
    print(f"Started at: {metric.started_at}")
    print(f"Finished at: {metric.finished_at}")

    print("\nStep metrics:")
    for step in metric.steps:
        print(
            f"- {step.step_name}: {step.status} "
            f"rows={step.row_count} "
            f"error={step.error_message} "
            f"({step.started_at} -> {step.finished_at})"
        )