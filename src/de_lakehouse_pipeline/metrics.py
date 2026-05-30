from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
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

    def to_dict(self) -> dict:
        data = asdict(self)
        data["duration_seconds"] = duration_seconds(self.started_at, self.finished_at)
        return data


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

    def to_dict(self) -> dict:
        data = asdict(self)
        data["steps"] = [step.to_dict() for step in self.steps]
        data["duration_seconds"] = duration_seconds(self.started_at, self.finished_at)
        return data

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)


def duration_seconds(started_at: str, finished_at: str | None) -> float | None:
    if finished_at is None:
        return None

    start = datetime.fromisoformat(started_at)
    finish = datetime.fromisoformat(finished_at)
    return round((finish - start).total_seconds(), 6)
