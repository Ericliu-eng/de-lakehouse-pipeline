
def upsert_stock_prices(conn, rows: list[tuple]) -> None:
    """
    Insert or update stock price rows into market_bars.
    """
    sql = """
        INSERT INTO market_bars (
            ts, symbol, open, high, low, close, volume,source
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (ts, symbol)
        DO UPDATE SET 
        open = EXCLUDED.open,
        high = EXCLUDED.high,
        low = EXCLUDED.low,
        close = EXCLUDED.close,
        volume = EXCLUDED.volume,
        source= EXCLUDED.source
    """
#EXCLUDED.open = 新传进来的 open
    with conn.cursor() as cur:
        #executemany = 
        #       for row in rows:
             #  cur.execute(sql, row)
        #
        cur.executemany(sql, rows)
    conn.commit()


def should_update_watermark_after_load(load_success: bool) -> bool:
    """Watermark should only move forward after a successful load."""
    return load_success