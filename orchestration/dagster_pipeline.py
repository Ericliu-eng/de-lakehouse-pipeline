from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class StepResult:
    step_name: str
    status: str
    started_at: str
    finished_at: str


def run_step(step_name: str) -> StepResult:
    started_at = datetime.now(timezone.utc).isoformat()

    try:
        print(f"Running step: {step_name}")

        # Placeholder for the real pipeline step.
        # Later this can call ingest, load, transform, quality checks, and marts.

        status = "success"

    except Exception as exc:
        status = "failed"
        print(f"Step failed: {step_name}")
        print(f"Error: {exc}")

    finished_at = datetime.now(timezone.utc).isoformat()

    return StepResult(
        step_name=step_name,
        status=status,
        started_at=started_at,
        finished_at=finished_at,
    )

def run_orchestrated_pipeline() -> list[StepResult]:
    steps = [
        "ingest_raw_stock_data",
        "load_raw_data_to_database",
        "run_transformations",
        "run_quality_checks",
        "build_marts",
    ]

    results = []

    for step in steps:
        result = run_step(step)
        results.append(result)

    return results


if __name__ == "__main__":
    results = run_orchestrated_pipeline()

    print("\nPipeline run summary:")
    for result in results:
        print(
            f"- {result.step_name}: {result.status} "
            f"({result.started_at} -> {result.finished_at})"
        )