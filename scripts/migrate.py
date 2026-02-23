from __future__ import annotations

from pathlib import Path

from de_lakehouse_pipeline.db import load_db_config, wait_for_db, connect


def run_sql_file(path: Path) -> None:
    sql = path.read_text(encoding="utf-8")
    cfg = load_db_config()
    wait_for_db(cfg, timeout_s=60)

    with connect(cfg) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    init_sql = root / "scripts" / "init_db.sql"
    seed_sql = root / "scripts" / "seed.sql"

    print("Running migrations...")
    run_sql_file(init_sql)
    print(f"Applied: {init_sql}")

    print("Seeding data...")
    run_sql_file(seed_sql)
    print(f"Applied: {seed_sql}")

    print("Done.")


if __name__ == "__main__":
    main()