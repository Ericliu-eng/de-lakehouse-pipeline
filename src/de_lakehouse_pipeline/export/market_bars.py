from __future__ import annotations

from pathlib import Path
from typing import Any
import pandas as pd

from de_lakehouse_pipeline.load.db.connection import (
    load_db_config,
    connect,
)


def fetch_market_bars(symbol: str | None = None) -> list[dict[str, Any]]:
    """Fetch market_bars rows from Postgres."""

    sql = """
        SELECT ts, symbol, open, high, low, close, volume, source
        FROM market_bars
    """
    params = ()

    if symbol is not None:
        sql += " WHERE symbol = %s"
        params = (symbol,)

    sql += " ORDER BY symbol, ts"

    with connect(load_db_config()) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()

    return [
        {
            "ts": row[0],
            "symbol": row[1],
            "open": row[2],
            "high": row[3],
            "low": row[4],
            "close": row[5],
            "volume": row[6],
            "source": row[7],
        }
        for row in rows
    ]


def write_market_bars_csv(
    output_path: str | Path,
    symbol: str | None = None,
) -> Path:
    """Write market_bars rows to a CSV file."""
    path = Path(output_path)

    rows = fetch_market_bars(symbol=symbol)
    
    path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows)
    df = df.rename(columns={"ts": "event_ts"})

    df["snapshot_id"] = path.stem
    df["ingested_at"] = pd.Timestamp.utcnow()

    df.to_csv(path, index=False)

    return path


def run_export(output_path: str | Path, symbol: str | None = None) -> Path:
    """Entry point for exporting market_bars."""
    return write_market_bars_csv(output_path=output_path, symbol=symbol)


def main():
    output_path = "export/market_bars.csv"
    exported_path = run_export(output_path=output_path)



if __name__ == "__main__":
    main()