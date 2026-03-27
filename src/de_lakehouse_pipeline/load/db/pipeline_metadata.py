def get_last_watermark(conn, source: str, symbol: str):
    sql = """
    SELECT last_watermark
    FROM pipeline_metadata
    WHERE source = %s
    AND symbol = %s
    LIMIT 1
    """

    with conn.cursor() as cur:
        cur.execute(sql, (source, symbol))
        row = cur.fetchone()

    return row[0] if row else None


def upsert_watermark(
    conn,
    source: str,
    symbol: str,
    last_watermark,
    last_row_count: int,
    status: str
):
    sql = """
    INSERT INTO pipeline_metadata (
        source,
        symbol,
        last_watermark,
        last_row_count,
        status
    )
    VALUES (%s, %s, %s, %s, %s)
    ON CONFLICT (source, symbol)
    DO UPDATE SET
        last_watermark = EXCLUDED.last_watermark,
        last_row_count = EXCLUDED.last_row_count,
        status = EXCLUDED.status,
        updated_at = CURRENT_TIMESTAMP
    """

    with conn.cursor() as cur:
        cur.execute(
            sql,
            (source, symbol, last_watermark, last_row_count, status)
        )
        conn.commit()
    
