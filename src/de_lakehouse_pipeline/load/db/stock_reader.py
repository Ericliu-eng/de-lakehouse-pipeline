from de_lakehouse_pipeline.load.db.connection import load_db_config, connect


def load_completed_market_dates(symbol: str) -> set[str]:
    sql = """
        SELECT DISTINCT DATE(ts)
        FROM market_bars
        WHERE symbol = %s
        ORDER BY 1
    """

    with connect(load_db_config()) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (symbol,))
            rows = cur.fetchall()

    return {row[0].isoformat() for row in rows}