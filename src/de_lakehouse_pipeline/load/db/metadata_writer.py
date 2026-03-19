def insert_load_metadata(conn, payload: dict) -> None:
    sql = """
    INSERT INTO load_metadata (
        source,
        load_date,
        version,
        record_count,
        recorded_at
    )
    VALUES (%s, %s, %s, %s, %s)
    """

    with conn.cursor() as cur:
        cur.execute(
            sql,
            (
                payload["source"],
                payload["load_date"],
                payload["version"],
                payload["record_count"],
                payload["recorded_at"],
            ),
        )
    conn.commit()