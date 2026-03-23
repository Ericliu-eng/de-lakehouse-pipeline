from __future__ import annotations
from pathlib import Path
from de_lakehouse_pipeline.load.db.connection import load_db_config, wait_for_db, connect


def run_sql_file(conn, path: Path) -> None:
    sql = path.read_text(encoding="utf-8").strip()
    if not sql:
        return
    #print("Running:", path)
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    seed_file = root / "scripts" / "seed.sql"

    cfg = load_db_config()
    wait_for_db(cfg, timeout_s=60)

    with connect(cfg) as conn:
        run_sql_file(conn, seed_file)


if __name__ == "__main__":
    main()