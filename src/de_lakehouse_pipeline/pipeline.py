from __future__ import annotations

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
from de_lakehouse_pipeline.transform.incremental import get_max_timestamp, filter_new_rows

logger = logging.getLogger(__name__)


def today_time() -> str:
    return date.today().isoformat()


def run_stock_for_date(target_date: date,symbol: str = "AAPL",root: Path | None = None,) -> Path:
    logger.info("Starting stock pipeline for %s", target_date.isoformat())
    try:
        logger.info("Fetching stock data for symbol=%s", symbol)
        data = fetch_daily_stock(symbol)

        file_path = save_raw_data(data, "stock", root)
        logger.info("Saved raw stock data to %s", file_path)

        raw_data = load_raw_stock_json(file_path)
        logger.info("Loaded raw stock json from %s", file_path)

        db_rows = parse_alpha_vantage_daily(raw_data)

        target_rows = [
            row for row in db_rows
            if row[0].date() == target_date
        ]
        logger.info(
            "Filtered transformed rows to %d row(s) for %s",
            len(target_rows),
            target_date.isoformat(),
        )

        if not target_rows:
            logger.info("No rows found for target date %s", target_date.isoformat())
            return file_path

        cfg = load_db_config()
        wait_for_db(cfg, timeout_s=60)

        with connect(cfg) as conn:
            last_ts = get_last_watermark(conn, "alpha_vantage", symbol)

            new_rows = filter_new_rows(rows=target_rows, last_watermark=last_ts)
            if not new_rows:
                logger.info("No new rows to load for %s", target_date.isoformat())
                return file_path

            upsert_stock_prices(conn, new_rows)
            max_ts = get_max_timestamp(new_rows)

            upsert_watermark(
                conn,
                "alpha_vantage",
                symbol,
                last_watermark=max_ts,
                last_row_count=len(new_rows),
                status="success",
            )

            metadata_payload = record_load(
                source="alpha_vantage",
                load_date=today_time(),
                version=today_time(),
                record_count=len(new_rows),
            )
            insert_load_metadata(conn, metadata_payload)

        logger.info("Stock pipeline finished successfully for %s", target_date.isoformat())
        return file_path

    except Exception:
        logger.exception("Stock pipeline failed for %s", target_date.isoformat())
        raise