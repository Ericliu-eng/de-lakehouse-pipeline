from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from zoneinfo import ZoneInfo
from de_lakehouse_pipeline.quality.schema_validation import (
    validate_stock_row_schema,
)

@dataclass(frozen=True)
class StagedMarketBar:
    ts: datetime
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    source: str = "alpha_vantage"


MARKET_TIME_ZONE = "US/Eastern"

ALPHA_VANTAGE_FIELD_MAP = {
    "open": "1. open",
    "high": "2. high",
    "low": "3. low",
    "close": "4. close",
    "volume": "5. volume",
}


def stage_alpha_vantage_daily(payload: dict) -> list[StagedMarketBar]:
    # dict.get(key, default)
    meta = payload.get("Meta Data", {})

    symbol = _normalize_symbol(meta.get("2. Symbol"))
    tz_name = meta.get("5. Time Zone", "US/Eastern")
    series = payload.get("Time Series (Daily)", {})

    rows = []

    for dt_str, values in series.items():
        canonical_row = {
            "ts": datetime.strptime(dt_str, "%Y-%m-%d").replace(
                tzinfo=ZoneInfo(tz_name)
            ),
            "symbol": symbol,
        }

        for field_name, source_field_name in ALPHA_VANTAGE_FIELD_MAP.items():
            if source_field_name in values:
                canonical_row[field_name] = values[source_field_name]

        validate_stock_row_schema(canonical_row)

        rows.append(
            StagedMarketBar(
                ts=canonical_row["ts"],
                symbol=canonical_row["symbol"],
                open=float(canonical_row["open"]),
                high=float(canonical_row["high"]),
                low=float(canonical_row["low"]),
                close=float(canonical_row["close"]),
                volume=int(canonical_row["volume"]),
            )
        )

    return rows


TIINGO_PRICE_FIELDS = ("open", "high", "low", "close", "volume")


def stage_tiingo_daily(prices: list[dict], symbol: str) -> list[StagedMarketBar]:
    """Stage unadjusted Tiingo bars on the same grain as Alpha Vantage rows.

    Tiingo labels each trading day as UTC midnight; the warehouse stores daily
    bars at US/Eastern midnight, so only the calendar date is kept.
    """
    symbol = _normalize_symbol(symbol)
    rows = []

    for bar in prices:
        canonical_row = {"symbol": symbol}
        if bar.get("date"):
            trading_date = date.fromisoformat(str(bar["date"])[:10])
            canonical_row["ts"] = datetime.combine(
                trading_date, time(), tzinfo=ZoneInfo(MARKET_TIME_ZONE)
            )

        for field_name in TIINGO_PRICE_FIELDS:
            if field_name in bar:
                canonical_row[field_name] = bar[field_name]

        validate_stock_row_schema(canonical_row)

        rows.append(
            StagedMarketBar(
                ts=canonical_row["ts"],
                symbol=symbol,
                open=float(canonical_row["open"]),
                high=float(canonical_row["high"]),
                low=float(canonical_row["low"]),
                close=float(canonical_row["close"]),
                volume=int(canonical_row["volume"]),
                source="tiingo",
            )
        )

    return rows


def to_db_tuple(row: StagedMarketBar) -> tuple:
    return (
        row.ts,
        row.symbol,
        row.open,
        row.high,
        row.low,
        row.close,
        row.volume,
        row.source
    )


def staged_rows_to_db_tuples(rows: list[StagedMarketBar]) -> list[tuple]:
    return [to_db_tuple(row) for row in rows]


def _normalize_symbol(symbol: str | None) -> str:
    if symbol is None or not symbol.strip():
        raise ValueError("Missing stock symbol in Alpha Vantage metadata.")
    return symbol.strip().upper()
