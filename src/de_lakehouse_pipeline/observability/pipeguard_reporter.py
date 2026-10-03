"""Report finished pipeline runs to PipeGuard without ever failing the pipeline.

PipeGuard keeps run history across pipelines and adds the one check a run cannot
make about itself: whether its row count collapsed compared with earlier runs.
This module sends it what only the pipeline knows — timings, the row count, and
the results of the in-batch quality checks.

Reporting is a side channel. The run is already recorded in this project's own
``pipeline_runs`` table before anything is sent, and PipeGuard may be asleep on
a free instance and take a minute to answer. So nothing here may raise into the
pipeline or hold it up for long: an unreachable or slow monitor costs one missing
report, never a failed load.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from uuid import UUID

import requests

from de_lakehouse_pipeline.metrics import PipelineMetric
from de_lakehouse_pipeline.quality.checks import CheckResult

logger = logging.getLogger(__name__)

URL_ENV = "PIPEGUARD_API_URL"
API_KEY_ENV = "PIPEGUARD_API_KEY"
TIMEOUT_ENV = "PIPEGUARD_TIMEOUT_SECONDS"
DEFAULT_TIMEOUT_SECONDS = 5.0

_ACCEPTED = {200, 201}


@dataclass(frozen=True)
class PipeGuardConfig:
    url: str
    api_key: str
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS


def load_pipeguard_config(env: Mapping[str, str] | None = None) -> PipeGuardConfig | None:
    """Read reporting settings, or return None when reporting is not set up.

    Both the URL and the key are required; with either missing, reporting is off
    and the pipeline behaves exactly as it did before this module existed.
    """
    env = os.environ if env is None else env
    url = env.get(URL_ENV, "").strip().rstrip("/")
    api_key = env.get(API_KEY_ENV, "").strip()
    if not url or not api_key:
        return None

    try:
        timeout = float(env.get(TIMEOUT_ENV, DEFAULT_TIMEOUT_SECONDS))
    except ValueError:
        timeout = DEFAULT_TIMEOUT_SECONDS
    return PipeGuardConfig(url=url, api_key=api_key, timeout_seconds=timeout)


def build_run_report(
    *,
    metric: PipelineMetric,
    external_run_id: UUID | str,
    rows_processed: int,
    checks: Iterable[CheckResult] = (),
) -> dict:
    """Translate a finished run into PipeGuard's ``POST /runs`` payload.

    ``external_run_id`` is the UUID this project already stored for the run, so
    a report that is sent again is recognised as the same run instead of being
    counted twice.
    """
    if metric.finished_at is None:
        raise ValueError("a run must be finished before it is reported")

    failed_step = next((step for step in metric.steps if step.status == "failed"), None)
    return {
        "pipeline_name": metric.pipeline_name,
        "external_run_id": str(external_run_id),
        "status": "SUCCESS" if metric.status == "success" else "FAILED",
        "started_at": metric.started_at,
        "finished_at": metric.finished_at,
        "rows_processed": rows_processed,
        "error_type": failed_step.error_type if failed_step else None,
        "error_message": failed_step.error_message if failed_step else None,
        "checks": [_check_payload(result) for result in checks],
    }


def _check_payload(result: CheckResult) -> dict:
    # Every check here passes only when no row violates it, so the violating row
    # count is the measured value and zero is the threshold.
    return {
        "check_name": result.check_name,
        "status": "PASS" if result.passed else "FAIL",
        "metric_value": float(result.failed_rows),
        "threshold": 0.0,
        "message": result.details or f"{result.check_name} on {result.table_name}",
    }


def report_run(
    report: dict,
    config: PipeGuardConfig | None = None,
    *,
    session=requests,
) -> bool:
    """Send one run report. Returns whether PipeGuard accepted it; never raises.

    ``200`` means PipeGuard already had this run and the report was a retry; it
    counts as accepted. Anything else is logged and dropped.
    """
    config = config if config is not None else load_pipeguard_config()
    if config is None:
        logger.debug("PipeGuard reporting is not configured; skipping run report")
        return False

    try:
        response = session.post(
            f"{config.url}/runs",
            json=report,
            headers={"X-API-Key": config.api_key},
            timeout=config.timeout_seconds,
        )
    except requests.RequestException as exc:
        logger.warning(
            "Could not reach PipeGuard; run %s was not reported: %s",
            report.get("external_run_id"),
            exc,
        )
        return False

    if response.status_code in _ACCEPTED:
        logger.info(
            "Reported run %s to PipeGuard (HTTP %s)",
            report.get("external_run_id"),
            response.status_code,
        )
        return True

    logger.warning(
        "PipeGuard rejected run %s with HTTP %s: %s",
        report.get("external_run_id"),
        response.status_code,
        response.text[:300],
    )
    return False
