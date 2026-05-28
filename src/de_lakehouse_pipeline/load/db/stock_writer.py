
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
#EXCLUDED.open = 新传进来的 open
    with conn.cursor() as cur:
        #executemany = 
        #       for row in rows:
             #  cur.execute(sql, row)
        #
        cur.executemany(sql, rows)
    conn.commit()