from dagster import Definitions, Field, In, Nothing, Out, ScheduleDefinition, job, op

from de_lakehouse_pipeline.pipeline import run_stock
from de_lakehouse_pipeline.quality.checks import run_stock_quality_checks
from de_lakehouse_pipeline.load.db.connection import load_db_config, wait_for_db, connect
from de_lakehouse_pipeline.transform.marts.mart_daily_symbol_summary import run_daily_summary
from de_lakehouse_pipeline.transform.marts.mart_symbol_latest_price import run_latest_price
from de_lakehouse_pipeline.transform.marts.mart_symbol_volume_rank import run_symbol_volume



#from dagster
@op(config_schema={"symbol": Field(str, default_value="AAPL")}, out=Out(str))
def ingest_stock(context) -> str:
    symbol = context.op_config["symbol"]
    run_stock(symbol)
    return symbol

@op(ins={"symbol": In(str)}, out=Out(Nothing))
def run_quality_checks(context, symbol: str):
    cfg = load_db_config()
    wait_for_db(cfg, timeout_s=60)

    with connect(cfg) as conn:
        results = run_stock_quality_checks(conn, symbol=symbol)

    failed = [result for result in results if not result.passed]
    if failed:
        details = "; ".join(
            f"{result.check_name}: {result.details}"
            for result in failed
        )
        raise RuntimeError(details)

    context.log.info(f"Quality checks passed: {len(results)}")


@op(ins={"quality_done": In(Nothing)})
def build_marts(context):
    
    cfg = load_db_config()
    wait_for_db(cfg, timeout_s=60)

    with connect(cfg) as conn:
        run_daily_summary(conn)
        run_latest_price(conn)
        run_symbol_volume(conn)
        conn.commit()

    context.log.info("Marts built successfully")


@job
def stock_lakehouse_job():
    quality_done = run_quality_checks(ingest_stock())
    build_marts(quality_done)


daily_stock_lakehouse_schedule = ScheduleDefinition(
    job=stock_lakehouse_job,
    cron_schedule="0 8 * * *",
    name="daily_stock_lakehouse_schedule",
)

defs = Definitions(
    jobs=[stock_lakehouse_job],
    schedules=[daily_stock_lakehouse_schedule],
)
