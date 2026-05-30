from orchestration.dagster_pipeline import run_orchestrated_pipeline, run_step


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
    assert metric.error_message == "boom"


def test_orchestrated_pipeline_stops_after_failed_step(monkeypatch) -> None:
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
