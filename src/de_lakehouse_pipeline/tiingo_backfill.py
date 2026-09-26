"""Backfill long price history from Tiingo without touching daily rows.

Alpha Vantage remains the daily incremental source. Tiingo fills dates that
are not in the warehouse yet: bars already present for a (ts, symbol) are kept
as loaded, and overlapping days are only used to compare the two sources'
close prices.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from de_lakehouse_pipeline.ingest.cloud_storage import upload_raw_payload_if_enabled
from de_lakehouse_pipeline.ingest.io import save_raw_data
from de_lakehouse_pipeline.ingest.tiingo_client import DEFAULT_HISTORY_START, fetch_tiingo_daily
from de_lakehouse_pipeline.load.db.connection import connect, load_db_config, wait_for_db
from de_lakehouse_pipeline.load.db.metadata_writer import insert_load_metadata
from de_lakehouse_pipeline.load.db.pipeline_metadata import upsert_watermark
from de_lakehouse_pipeline.load.db.stock_writer import insert_missing_stock_prices
from de_lakehouse_pipeline.load.metadata import record_load
from de_lakehouse_pipeline.quality.reconciliation import CloseReconciliation, reconcile_close_prices
from de_lakehouse_pipeline.transform.incremental import get_max_timestamp
from de_lakehouse_pipeline.transform.staging.staging_market_bars import (
    stage_tiingo_daily,
    staged_rows_to_db_tuples,
)

logger = logging.getLogger(__name__)

SOURCE = "tiingo"


@dataclass(frozen=True)
class TiingoBackfillResult:
    symbol: str
    fetched_rows: int
    inserted_rows: int
    first_date: date | None
    last_date: date | None
    reconciliation: CloseReconciliation

    @property
    def skipped_rows(self) -> int:
        return self.fetched_rows - self.inserted_rows


def load_other_source_closes(conn, symbol: str) -> dict[datetime, float]:
    rows = conn.execute(
        "SELECT ts, close FROM market_bars WHERE symbol = %s AND source <> %s",
        (symbol, SOURCE),
    ).fetchall()
    return {ts: float(close) for ts, close in rows}


def run_tiingo_backfill(
    symbol: str,
    start_date: date = DEFAULT_HISTORY_START,
    end_date: date | None = None,
    root: Path | None = None,
    s3_client=None,
    payload: list[dict] | None = None,
) -> TiingoBackfillResult:
    symbol = symbol.strip().upper()
    logger.info("Starting Tiingo backfill for symbol=%s", symbol)

    data = payload if payload is not None else fetch_tiingo_daily(symbol, start_date, end_date)
    run_date = date.today()
    file_path = save_raw_data(data, SOURCE, root, run_date, symbol=symbol)
    logger.info("Saved raw Tiingo data to %s", file_path)

    s3_uri = upload_raw_payload_if_enabled(
        payload=data,
        source=SOURCE,
        symbol=symbol,
        run_date=run_date,
        filename=f"{SOURCE}.json",
        s3_client=s3_client,
    )
    if s3_uri is not None:
        logger.info("Uploaded raw Tiingo data to %s", s3_uri.uri)

    db_rows = staged_rows_to_db_tuples(stage_tiingo_daily(data, symbol))
    cfg = load_db_config()
    wait_for_db(cfg, timeout_s=60)

    # Comparison, insert, watermark, and audit share one transaction.
    with connect(cfg) as conn:
        reconciliation = reconcile_close_prices(
            {row[0]: row[5] for row in db_rows},
            load_other_source_closes(conn, symbol),
        )
        inserted = insert_missing_stock_prices(conn, db_rows) if db_rows else 0

        if db_rows:
            upsert_watermark(
                conn,
                SOURCE,
                symbol,
                last_watermark=get_max_timestamp(db_rows),
                last_row_count=inserted,
                status="success",
            )
            insert_load_metadata(
                conn,
                record_load(
                    source=SOURCE,
                    load_date=run_date.isoformat(),
                    version=run_date.isoformat(),
                    record_count=inserted,
                ),
            )

    if not reconciliation.passed:
        logger.warning(
            "Tiingo closes differ from existing rows for symbol=%s on %d of %d overlapping day(s)",
            symbol,
            reconciliation.mismatched_days,
            reconciliation.overlap_days,
        )

    dates = sorted(row[0].date() for row in db_rows)
    result = TiingoBackfillResult(
        symbol=symbol,
        fetched_rows=len(db_rows),
        inserted_rows=inserted,
        first_date=dates[0] if dates else None,
        last_date=dates[-1] if dates else None,
        reconciliation=reconciliation,
    )
    logger.info(
        "Tiingo backfill finished for symbol=%s: %d fetched, %d inserted",
        symbol,
        result.fetched_rows,
        result.inserted_rows,
    )
    return result


def format_result(result: TiingoBackfillResult) -> str:
    rec = result.reconciliation
    overlap = (
        f"{rec.overlap_days} overlapping day(s), {rec.mismatched_days} beyond "
        f"{rec.tolerance_pct}% close difference (max {rec.max_diff_pct}%)"
        if rec.overlap_days
        else "no overlapping days"
    )
    return (
        f"{result.symbol}: fetched {result.fetched_rows} bar(s) "
        f"({result.first_date} to {result.last_date}), inserted {result.inserted_rows}, "
        f"kept {result.skipped_rows} existing; {overlap}"
    )
