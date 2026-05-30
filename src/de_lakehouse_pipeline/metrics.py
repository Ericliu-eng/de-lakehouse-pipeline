from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class StepMetric:
    step_name: str
    status: str
    started_at: str
    finished_at: str
    row_count: int | None = None
    error_message: str | None = None


@dataclass
class PipelineMetric:
    pipeline_name: str
    started_at: str
    finished_at: str | None = None
    status: str = "running"
    steps: list[StepMetric] = field(default_factory=list)

    def add_step(self, step_metric: StepMetric) -> None:
        self.steps.append(step_metric)

    def finish(self, status: str) -> None:
        self.status = status
        self.finished_at = utc_now()