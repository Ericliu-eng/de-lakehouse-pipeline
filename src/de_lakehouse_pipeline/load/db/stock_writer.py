
def upsert_stock_prices(conn, rows: list[tuple]) -> None:
    """
    Insert or update rows into stock_prices.
    """
    sql = """
        INSERT INTO market_bars (
            ts, symbol, open, high, low, close, volume
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (ts, symbol)
        DO UPDATE SET 
        open = EXCLUDED.open,
        high = EXCLUDED.high,
        low = EXCLUDED.low,
        close = EXCLUDED.close,
        volume = EXCLUDED.volume;
    """

    with conn.cursor() as cur:
        cur.executemany(sql, rows)
    conn.commit()