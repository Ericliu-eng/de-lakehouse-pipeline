from __future__ import annotations

import logging
from pathlib import Path
from datetime import date

from de_lakehouse_pipeline.ingest.market_data_client import fetch_daily_stock
from de_lakehouse_pipeline.load.loader import load_raw_stock_json
from de_lakehouse_pipeline.transform.staging.staging_market_bars import (
    stage_alpha_vantage_daily,
    staged_rows_to_db_tuples,
)
from de_lakehouse_pipeline.load.db.stock_writer import upsert_stock_prices
from de_lakehouse_pipeline.load.db.connection import load_db_config, wait_for_db, connect
from de_lakehouse_pipeline.load.metadata import record_load
from de_lakehouse_pipeline.load.db.metadata_writer import insert_load_metadata
from de_lakehouse_pipeline.ingest.cloud_storage import upload_raw_payload_if_enabled
from de_lakehouse_pipeline.ingest.io import save_raw_data
from de_lakehouse_pipeline.load.db.pipeline_metadata import get_last_watermark, upsert_watermark
from de_lakehouse_pipeline.transform.incremental import get_max_timestamp, filter_new_rows

logger = logging.getLogger(__name__)


def today_time() -> str:
    return date.today().isoformat()



def run_stock(symbol: str = "AAPL", root: Path | None = None) -> Path:
    logger.info("Starting stock pipeline for symbol=%s", symbol)

    try:
        logger.info("Fetching stock data for symbol=%s", symbol)
        #1.Use the client to retrieve the stocks you want.
        data = fetch_daily_stock(symbol)
        #2.save the raw data in local 
        file_path = save_raw_data(data,"stock", root)

        logger.info("Saved raw stock data to %s", file_path)
        #3.Upload to the cloud and return a URI.
        s3_uri = upload_raw_payload_if_enabled(
            payload=data,
            source="alpha_vantage",
            symbol=symbol,
            run_date=date.today(),
            filename="stock.json",
        )

        if s3_uri is not None:
            logger.info("Uploaded raw stock data to %s", s3_uri)
        #4.load local  json in to project
        raw_data = load_raw_stock_json(file_path)

        logger.info("Loaded raw stock json from %s", file_path)
        #5.form dict invert to tuple
        staged_rows = stage_alpha_vantage_daily(raw_data)
        db_rows = staged_rows_to_db_tuples(staged_rows)

        rows_to_check = db_rows

        logger.info(
            "Staged %d row(s) from raw stock json",
            len(rows_to_check),
        )

        if not rows_to_check:
            logger.info("No rows found in raw stock json")
            return file_path

        cfg = load_db_config()
        wait_for_db(cfg, timeout_s=60)

        with connect(cfg) as conn:
            #6.获取上一次 pipeline 已经处理到哪里了。
            last_ts = get_last_watermark(conn, "alpha_vantage", symbol)
            # If the stock is up-to-date  insert
            new_rows = filter_new_rows(
                rows=rows_to_check,
                last_watermark=last_ts,
            )

            if not new_rows:
                logger.info("No new rows to load for symbol=%s", symbol)
                return file_path
            #7.insert the lastest stock 
            upsert_stock_prices(conn, new_rows)
            #get the lastest date 
            max_ts = get_max_timestamp(new_rows)
            #inseet into pipeline_metadata table
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
            #8.insert the metadata record into load_metadata
            insert_load_metadata(conn, metadata_payload)

        logger.info(
            "Stock pipeline finished successfully for symbol=%s with %d new row(s)",
            symbol,
            len(new_rows),
        )
        return file_path

    except Exception:
        logger.exception("Stock pipeline failed for symbol=%s", symbol)
        raise

    
def run_stock_for_date(target_date: date,symbol: str = "AAPL",root: Path | None = None,) -> Path:
    logger.info("Starting stock pipeline for %s", target_date.isoformat())
    try:
        logger.info("Fetching stock data for symbol=%s", symbol)
        data = fetch_daily_stock(symbol)

        file_path = save_raw_data(data, "stock", root,target_date)
        logger.info("Saved raw stock data to %s", file_path)
        s3_uri = upload_raw_payload_if_enabled(
            payload=data,
            source="alpha_vantage",
            symbol=symbol,
            run_date=target_date,
            filename="stock.json",
        )
        if s3_uri is not None:
            logger.info("Uploaded raw stock data to %s", s3_uri)

        raw_data = load_raw_stock_json(file_path)
        logger.info("Loaded raw stock json from %s", file_path)

        staged_rows = stage_alpha_vantage_daily(raw_data)
        db_rows = staged_rows_to_db_tuples(staged_rows)

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
            last_ts = get_last_watermark(
                conn,
                "alpha_vantage",
                symbol,
            )

            # 回填目标日期，不使用 watermark 过滤
            rows_to_upsert = target_rows

            upsert_stock_prices(conn, rows_to_upsert)

            max_ts = get_max_timestamp(rows_to_upsert)

            # 防止历史回填导致 watermark 倒退
            if last_ts is None:
                watermark_to_save = max_ts
            else:
                watermark_to_save = max(last_ts, max_ts)

            upsert_watermark(
                conn,
                "alpha_vantage",
                symbol,
                last_watermark=watermark_to_save,
                last_row_count=len(rows_to_upsert),
                status="success",
            )

            metadata_payload = record_load(
                source="alpha_vantage",
                load_date=today_time(),
                version=today_time(),
                record_count=len(rows_to_upsert),
            )
            insert_load_metadata(conn, metadata_payload)

        logger.info("Stock pipeline finished successfully for %s", target_date.isoformat())
        return file_path

    except Exception:
        logger.exception("Stock pipeline failed for %s", target_date.isoformat())
        raise
