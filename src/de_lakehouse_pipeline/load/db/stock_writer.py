def upsert_stock_prices(conn, rows, source: str = "unknown"):
    normalized_rows = []

    for row in rows:
        if len(row) == 7:
            ts, symbol, open_, high, low, close, volume = row
            normalized_rows.append(
                (ts, symbol, open_, high, low, close, volume, source)
            )
        elif len(row) == 8:
            normalized_rows.append(row)
        else:
            raise ValueError(
                f"Expected row with 7 or 8 values, got {len(row)}: {row}"
            )

    sql = """
        INSERT INTO market_bars (
            ts, symbol, open, high, low, close, volume, source
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (ts, symbol) DO UPDATE SET
            open = EXCLUDED.open,
            high = EXCLUDED.high,
            low = EXCLUDED.low,
            close = EXCLUDED.close,
            volume = EXCLUDED.volume,
            source = EXCLUDED.source
    """

    with conn.cursor() as cur:
        cur.executemany(sql, normalized_rows)

def should_update_watermark_after_load(load_success: bool) -> bool:
    """Watermark should only move forward after a successful load."""
    return load_success