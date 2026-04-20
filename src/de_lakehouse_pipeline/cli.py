import argparse
import logging
from pathlib import Path
from datetime import date

from de_lakehouse_pipeline.ingest.market_data_client import fetch_daily_stock
from de_lakehouse_pipeline.load.loader import load_raw_stock_json
from de_lakehouse_pipeline.transform.transform_stock import parse_alpha_vantage_daily
from de_lakehouse_pipeline.load.db.stock_writer import upsert_stock_prices
from de_lakehouse_pipeline.load.db.connection import load_db_config, wait_for_db, connect
from de_lakehouse_pipeline.load.metadata import record_load
from de_lakehouse_pipeline.load.db.metadata_writer import insert_load_metadata
from de_lakehouse_pipeline.ingest.io import save_raw_data
from de_lakehouse_pipeline.load.db.pipeline_metadata import get_last_watermark, upsert_watermark
from de_lakehouse_pipeline.transform.incremental import get_max_timestamp,filter_new_rows
from de_lakehouse_pipeline.transform.marts.mart_daily_symbol_summary import run_daily_summary
from de_lakehouse_pipeline.transform.marts.mart_symbol_latest_price import run_latest_price
from de_lakehouse_pipeline.transform.marts.mart_symbol_volume_rank import run_symbol_volume

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

logger = logging.getLogger(__name__)
def today_time():
    return date.today().isoformat()

def run_stock(root: Path = None):
    logger.info("Starting stock pipeline")

    try:

        # Step 1: ingest
        logger.info("Fetching stock data for symbol=AAPL")
        data = fetch_daily_stock("AAPL")
       

        file_path = save_raw_data(data, "stock", root)
        logger.info("Saved raw stock data to %s", file_path)

        # Step 2: load raw json
        raw_data = load_raw_stock_json(file_path)
        logger.info("Loaded raw stock json from %s", file_path)

        # Step 3: transform
        db_rows = parse_alpha_vantage_daily(raw_data)
  
        logger.info("Transformed stock payload into %d rows", len(db_rows))

        # Step 4: connect db
        cfg = load_db_config()
        wait_for_db(cfg, timeout_s=60)

        with connect(cfg) as conn:
            logger.info("Writing stock rows into database")
                    
            last_ts = get_last_watermark(conn,"alpha_vantage","AAPL")
            # 1. filter
            new_rows  = filter_new_rows(rows=db_rows,last_watermark=last_ts)
            # 2. empty case
            if not new_rows:
                logger.info("No new rows to load")
                return file_path
            
            upsert_stock_prices(conn, new_rows)
            max_ts = get_max_timestamp(new_rows)

            upsert_watermark(
            conn,
            "alpha_vantage",
            "AAPL",
            last_watermark=max_ts,
            last_row_count=len(new_rows),
            status="success"
            )
            
            metadata_payload = record_load(
                source="alpha_vantage",
                load_date=today_time(),
                version=today_time(),
                record_count=len(db_rows),
            )

            logger.info("Recording load metadata: %s", metadata_payload)
            insert_load_metadata(conn, metadata_payload)

        logger.info("Stock pipeline finished successfully")
        return file_path

    except Exception:
        logger.exception("Stock pipeline failed")
        raise

def run_weather(city: str) -> None:
    #"Step 1: ingest"
    #data = fetch_current_weather(city)
    #file_path = save_raw_data(data,"weather")
    #"Step 2: load"
    #load_file = load_weather_file_to_db(file_path)
    print()

    #"Step 3: transform"
    #infor = trans_weather(load_file)
    #print(infor)

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
    parser.add_argument("command", choices=["run_stock", "run_weather", "run_marts"])
    parser.add_argument("--city", default="Berkeley,US")
    args = parser.parse_args()

    if args.command == "run_stock":
        run_stock()
    elif args.command == "run_weather":
        run_weather(args.city)
    elif args.command == "run_marts":
        run_marts()


if __name__ == "__main__":
    main()