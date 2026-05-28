import argparse
import logging

from datetime import date

from de_lakehouse_pipeline.load.db.connection import load_db_config, wait_for_db, connect
from de_lakehouse_pipeline.transform.marts.mart_daily_symbol_summary import run_daily_summary
from de_lakehouse_pipeline.transform.marts.mart_symbol_latest_price import run_latest_price
from de_lakehouse_pipeline.transform.marts.mart_symbol_volume_rank import run_symbol_volume
from de_lakehouse_pipeline.backfill import run_backfill, parse_iso_date, validate_date_range
from de_lakehouse_pipeline.pipeline import run_stock

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

logger = logging.getLogger(__name__)
def today_time():
    return date.today().isoformat()



def run_marts() -> None:
    logger.info("Starting marts pipeline")

    cfg = load_db_config()
    wait_for_db(cfg, timeout_s=60)

    with connect(cfg) as conn:
        run_daily_summary(conn)
        run_latest_price(conn)
        run_symbol_volume(conn)
        conn.commit()

    logger.info("Marts pipeline finished successfully")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["run_stock", "run_marts", "backfill"])
    #backfill
    parser.add_argument("--start")
    parser.add_argument("--end")
    args = parser.parse_args()

    if args.command == "run_stock":
        run_stock()
    elif args.command == "run_marts":
        run_marts()
    #backfill
    elif args.command == "backfill":
        if not args.start or not args.end:
            raise ValueError("backfill requires --start and --end")
        start = parse_iso_date(args.start)
        end = parse_iso_date(args.end)
        validate_date_range(start, end)
        run_backfill(start, end)


if __name__ == "__main__":
    main()