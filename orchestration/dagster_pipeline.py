from __future__ import annotations

import argparse
import logging
from collections.abc import Callable, Sequence
from datetime import datetime

from de_lakehouse_pipeline.load.db.connection import connect, load_db_config, wait_for_db
from de_lakehouse_pipeline.logging_utils import configure_logging
from de_lakehouse_pipeline.metrics import PipelineMetric, StepMetric, utc_now
from de_lakehouse_pipeline.observability.pipeguard_reporter import build_run_report, report_run
from de_lakehouse_pipeline.observability.run_repository import (
    PipelineRunHandle,
    finish_pipeline_run,
    start_pipeline_run,
)
from de_lakehouse_pipeline.pipeline import load_stock
from de_lakehouse_pipeline.symbols import normalize_symbol
from de_lakehouse_pipeline.quality.checks import CheckResult, run_stock_quality_checks
from de_lakehouse_pipeline.transform.marts.mart_daily_symbol_summary import run_daily_summary
from de_lakehouse_pipeline.transform.marts.mart_symbol_latest_price import run_latest_price
from de_lakehouse_pipeline.transform.marts.mart_symbol_volume_rank import run_symbol_volume


logger = logging.getLogger(__name__)


def run_step(step_name: str, fn: Callable[[], int | None]) -> StepMetric:
    started_at = utc_now()

    try:
        logger.info("Starting orchestration step", extra={"step_name": step_name})
        row_count = fn()
        logger.info(
            "Finished orchestration step",
            extra={"step_name": step_name, "status": "success", "row_count": row_count},
        )

        return StepMetric(
            step_name=step_name,
            status="success",
            started_at=started_at,
            finished_at=utc_now(),
            row_count=row_count,
            error_type=None,
            error_message=None,
        )
    except Exception as exc:
        logger.exception(
            "Orchestration step failed",
            extra={"step_name": step_name, "status": "failed"},
        )

        return StepMetric(
            step_name=step_name,
            status="failed",
            started_at=started_at,
            finished_at=utc_now(),
            row_count=None,
            error_type=type(exc).__name__,
            error_message=str(exc),
        )


def run_orchestrated_pipeline(symbol: str = "AAPL") -> PipelineMetric:
    symbol = normalize_symbol(symbol)
    pipeline_name = "market_data_lakehouse_pipeline"
    logger.info(
        "Starting orchestrated pipeline",
        extra={"pipeline_name": pipeline_name, "symbol": symbol},
    )

    pipeline_metric = PipelineMetric(
        pipeline_name=pipeline_name,
        started_at=utc_now(),
    )
    run_handle = _start_pipeline_run_record(pipeline_metric, symbol=symbol)
    # Filled by the quality step, including when it fails, so a run that stops
    # on bad data still reports which checks it failed.
    quality_results: list[CheckResult] = []

    stock_step = run_step("run_stock_pipeline", lambda: _run_stock_pipeline(symbol))
    pipeline_metric.add_step(stock_step)
    if stock_step.status == "failed":
        return _complete_pipeline_run(
            run_handle, pipeline_metric, status="failed", checks=quality_results
        )

    quality_step = run_step(
        "run_quality_checks",
        lambda: _run_quality_checks(symbol, quality_results),
    )
    pipeline_metric.add_step(quality_step)
    if quality_step.status == "failed":
        return _complete_pipeline_run(
            run_handle, pipeline_metric, status="failed", checks=quality_results
        )

    marts_step = run_step("build_marts", _build_marts)
    pipeline_metric.add_step(marts_step)
    if marts_step.status == "failed":
        return _complete_pipeline_run(
            run_handle, pipeline_metric, status="failed", checks=quality_results
        )

    _complete_pipeline_run(
        run_handle, pipeline_metric, status="success", checks=quality_results
    )
    logger.info(
        "Finished orchestrated pipeline",
        extra={
            "pipeline_name": pipeline_metric.pipeline_name,
            "status": pipeline_metric.status,
            "step_count": len(pipeline_metric.steps),
        },
    )

    return pipeline_metric


def _complete_pipeline_run(
    handle: PipelineRunHandle,
    metric: PipelineMetric,
    *,
    status: str,
    checks: Sequence[CheckResult] = (),
) -> PipelineMetric:
    metric.finish(status=status)
    # The local record is the source of truth and is written first; the report
    # to PipeGuard is a best-effort copy sent afterwards.
    _finish_pipeline_run_record(handle, metric)
    _report_to_pipeguard(handle, metric, checks)
    return metric


def _report_to_pipeguard(
    handle: PipelineRunHandle,
    metric: PipelineMetric,
    checks: Sequence[CheckResult],
) -> None:
    # report_run already absorbs network failures. This guard is for everything
    # else, so that no defect in reporting can change the outcome of a load.
    try:
        report = build_run_report(
            metric=metric,
            external_run_id=handle.external_run_id,
            rows_processed=_rows_processed(metric),
            checks=checks,
        )
        report_run(report)
    except Exception:
        logger.exception("Unexpected error while reporting the run to PipeGuard")


def _rows_processed(metric: PipelineMetric) -> int:
    ingest_step = next(
        (step for step in metric.steps if step.step_name == "run_stock_pipeline"),
        None,
    )
    return (ingest_step.row_count or 0) if ingest_step else 0


def _start_pipeline_run_record(
    metric: PipelineMetric,
    *,
    symbol: str,
) -> PipelineRunHandle:
    cfg = load_db_config()
    wait_for_db(cfg, timeout_s=60)

    with connect(cfg) as conn:
        handle = start_pipeline_run(
            conn,
            pipeline_name=metric.pipeline_name,
            source="alpha_vantage",
            symbol=symbol,
            started_at=datetime.fromisoformat(metric.started_at),
        )
        conn.commit()

    return handle


def _finish_pipeline_run_record(
    handle: PipelineRunHandle,
    metric: PipelineMetric,
) -> None:
    if metric.finished_at is None:
        raise ValueError("pipeline metric must be finished before persistence")

    failed_step = next((step for step in metric.steps if step.status == "failed"), None)
    quality_step = next(
        (step for step in metric.steps if step.step_name == "run_quality_checks"),
        None,
    )
    quality_status = "NOT_EVALUATED"
    if quality_step is not None:
        quality_status = "PASS" if quality_step.status == "success" else "FAIL"

    cfg = load_db_config()
    wait_for_db(cfg, timeout_s=60)

    with connect(cfg) as conn:
        finish_pipeline_run(
            conn,
            run_id=handle.id,
            status=metric.status,
            quality_status=quality_status,
            finished_at=datetime.fromisoformat(metric.finished_at),
            rows_processed=_rows_processed(metric),
            error_type=failed_step.error_type if failed_step else None,
            error_message=failed_step.error_message if failed_step else None,
        )
        conn.commit()


def _run_stock_pipeline(symbol: str) -> int:
    # Rows received from the source, not rows newly loaded: the load is
    # incremental, so new rows are about one per trading day and zero on
    # weekends, which would make every weekend look like a collapse.
    return load_stock(symbol=symbol).rows_received


def _run_quality_checks(symbol: str, results: list[CheckResult] | None = None) -> int:
    cfg = load_db_config()
    wait_for_db(cfg, timeout_s=60)

    with connect(cfg) as conn:
        checks = run_stock_quality_checks(conn, symbol=symbol)

    if results is not None:
        results.extend(checks)

    failed_results = [result for result in checks if not result.passed]
    if failed_results:
        raise RuntimeError(_format_quality_failures(failed_results))

    return len(checks)


def _build_marts() -> None:
    cfg = load_db_config()
    wait_for_db(cfg, timeout_s=60)

    with connect(cfg) as conn:
        run_daily_summary(conn)
        run_latest_price(conn)
        run_symbol_volume(conn)
        conn.commit()


def _format_quality_failures(results: list[CheckResult]) -> str:
    return "; ".join(
        f"{result.check_name} on {result.table_name}: {result.details}"
        for result in results
    )


def _print_summary(metric: PipelineMetric) -> None:
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

    print("\nMetrics JSON:")
    print(metric.to_json())


def main() -> None:
    configure_logging()
    parser = argparse.ArgumentParser(description="Run local pipeline orchestration.")
    parser.add_argument("--symbol", default="AAPL")
    args = parser.parse_args()

    metric = run_orchestrated_pipeline(symbol=args.symbol)
    _print_summary(metric)
    if metric.status != "success":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
