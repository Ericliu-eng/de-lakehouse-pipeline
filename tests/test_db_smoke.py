from __future__ import annotations

from de_lakehouse_pipeline.db  import load_db_config, wait_for_db, connect


def test_db_smoke_can_query_users() -> None:
    cfg = load_db_config()
    wait_for_db(cfg, timeout_s=60)

    with connect(cfg) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT name FROM users ORDER BY name;")
            rows = cur.fetchall()

    names = [r[0] for r in rows]
    assert "Alice" in names
    assert "Bob" in names