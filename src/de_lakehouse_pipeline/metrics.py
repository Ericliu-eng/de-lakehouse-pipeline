from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

#metrics  = 指标 / 度量值。
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



@dataclass(frozen=True)
class SlaConfig:
    max_freshness_minutes: int = 1440
    max_latency_seconds: float = 300.0
    max_failure_rate: float = 0.05


@dataclass(frozen=True)
class SlaReport:
    data_freshness_minutes: float | None
    pipeline_latency_seconds: float | None
    failure_rate: float
    passed: bool
    violations: list[str]

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)

def freshness_minutes(latest_data_at: str | None, checked_at: str) -> float | None:
    if latest_data_at is None:
        return None

    latest = datetime.fromisoformat(latest_data_at)
    checked = datetime.fromisoformat(checked_at)
    return round((checked - latest).total_seconds() / 60, 6)


def failure_rate(failed_runs: int, total_runs: int) -> float:
    if total_runs <= 0:
        return 0.0

    return round(failed_runs / total_runs, 6)


def build_sla_report(
    *,
    latest_data_at: str | None,
    checked_at: str,
    pipeline_started_at: str,
    pipeline_finished_at: str | None,
    failed_runs: int,
    total_runs: int,
    config: SlaConfig | None = None,
) -> SlaReport:
    config = config or SlaConfig()

    freshness = freshness_minutes(latest_data_at, checked_at)
    latency = duration_seconds(pipeline_started_at, pipeline_finished_at)
    failures = failure_rate(failed_runs, total_runs)

    violations: list[str] = []

    if freshness is None:
        violations.append("freshness_missing")
    elif freshness > config.max_freshness_minutes:
        violations.append("freshness_sla_breached")

    if latency is None:
        violations.append("latency_missing")
    elif latency > config.max_latency_seconds:
        violations.append("latency_sla_breached")

    if failures > config.max_failure_rate:
        violations.append("failure_rate_sla_breached")

    return SlaReport(
        data_freshness_minutes=freshness,
        pipeline_latency_seconds=latency,
        failure_rate=failures,
        passed=len(violations) == 0,
        violations=violations,
    )

RETRYABLE_ERROR_TYPES = {
    "timeout",
    "rate_limit",
    "connection",
    "temporary",
    "server_error",
}

NON_RETRYABLE_ERROR_TYPES = {
    "schema",
    "validation",
    "auth",
    "not_found",
    "bad_request",
}


def classify_failure(error_type: str) -> str:
    normalized = error_type.strip().lower()

    if normalized in RETRYABLE_ERROR_TYPES:
        return "retryable"

    if normalized in NON_RETRYABLE_ERROR_TYPES:
        return "non_retryable"

    return "unknown"