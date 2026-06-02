from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class StagedMarketBar:
    ts: datetime
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: int


def stage_alpha_vantage_daily(payload: dict) -> list[StagedMarketBar]:
    # dict.get(key, default)
    meta = payload.get("Meta Data", {})

    symbol = _normalize_symbol(meta.get("2. Symbol"))
    tz_name = meta.get("5. Time Zone", "US/Eastern")
    series = payload.get("Time Series (Daily)", {})

    rows = []
    for dt_str, values in series.items():
        ts = datetime.strptime(dt_str, "%Y-%m-%d").replace(
            tzinfo=ZoneInfo(tz_name)
        )
        rows.append(
            StagedMarketBar(
                ts=ts,
                symbol=symbol,
                open=float(values["1. open"]),
                high=float(values["2. high"]),
                low=float(values["3. low"]),
                close=float(values["4. close"]),
                volume=int(values["5. volume"]),
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
    )


def staged_rows_to_db_tuples(rows: list[StagedMarketBar]) -> list[tuple]:
    return [to_db_tuple(row) for row in rows]


def _normalize_symbol(symbol: str | None) -> str:
    if symbol is None or not symbol.strip():
        raise ValueError("Missing stock symbol in Alpha Vantage metadata.")
    return symbol.strip().upper()
