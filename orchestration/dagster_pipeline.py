from __future__ import annotations

import argparse
import logging
from collections.abc import Callable

from de_lakehouse_pipeline.load.db.connection import connect, load_db_config, wait_for_db
from de_lakehouse_pipeline.logging_utils import configure_logging
from de_lakehouse_pipeline.metrics import PipelineMetric, StepMetric, utc_now
from de_lakehouse_pipeline.pipeline import run_stock
from de_lakehouse_pipeline.quality.checks import CheckResult, run_stock_quality_checks
from de_lakehouse_pipeline.transform.marts.mart_daily_symbol_summary import run_daily_summary
from de_lakehouse_pipeline.transform.marts.mart_symbol_latest_price import run_latest_price
from de_lakehouse_pipeline.transform.marts.mart_symbol_volume_rank import run_symbol_volume


logger = logging.getLogger(__name__)


def run_step(step_name: str, fn: Callable[[], int | None]) -> StepMetric:
    started_at = utc_now()
    row_count = None

    try:
        logger.info("Starting orchestration step", extra={"step_name": step_name})
        row_count = fn()
        status = "success"
        error_message = None
        logger.info(
            "Finished orchestration step",
            extra={"step_name": step_name, "status": status, "row_count": row_count},
        )
    except Exception as exc:
        status = "failed"
        error_message = str(exc)
        logger.exception(
            "Orchestration step failed",
            extra={"step_name": step_name, "status": status},
        )

    finished_at = utc_now()

    return StepMetric(
        step_name=step_name,
        status=status,
        started_at=started_at,
        finished_at=finished_at,
        row_count=row_count,
        error_message=error_message,
    )


def run_orchestrated_pipeline(symbol: str = "AAPL") -> PipelineMetric:
    logger.info(
        "Starting orchestrated pipeline",
        extra={"pipeline_name": "market_data_lakehouse_pipeline", "symbol": symbol},
    )
    pipeline_metric = PipelineMetric(
        pipeline_name="market_data_lakehouse_pipeline",
        started_at=utc_now(),
    )

    steps: list[tuple[str, Callable[[], int | None]]] = [
        ("run_stock_pipeline", lambda: _run_stock_pipeline(symbol)),
        ("run_quality_checks", _run_quality_checks),
        ("build_marts", _build_marts),
    ]

    for step_name, step_fn in steps:
        step_metric = run_step(step_name, step_fn)
        pipeline_metric.add_step(step_metric)

        if step_metric.status == "failed":
            break

    failed_steps = [
        step for step in pipeline_metric.steps if step.status == "failed"
    ]
    final_status = "failed" if failed_steps else "success"
    pipeline_metric.finish(status=final_status)
    logger.info(
        "Finished orchestrated pipeline",
        extra={
            "pipeline_name": pipeline_metric.pipeline_name,
            "status": pipeline_metric.status,
            "step_count": len(pipeline_metric.steps),
        },
    )

    return pipeline_metric


def _run_stock_pipeline(symbol: str) -> None:
    run_stock(symbol=symbol)


def _run_quality_checks() -> int:
    cfg = load_db_config()
    wait_for_db(cfg, timeout_s=60)

    with connect(cfg) as conn:
        results = run_stock_quality_checks(conn)

    failed_results = [result for result in results if not result.passed]
    if failed_results:
        raise RuntimeError(_format_quality_failures(failed_results))

    return len(results)


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


if __name__ == "__main__":
    main()
