from __future__ import annotations

from pathlib import Path

from de_lakehouse_pipeline.load.db.connection import load_db_config, wait_for_db, connect


def run_sql_file(conn, path: Path) -> None:

    sql = path.read_text(encoding="utf-8").strip()
    if not sql:
        return  # ignore empty files safely
    print("Running:", path)
    with conn.cursor() as cur:
        cur.execute(sql)
        conn.commit()


def list_migration_files(migrations_dir: Path):
    return sorted(migrations_dir.glob("*.sql"))

def seed():
    root = Path(__file__).resolve().parents[1]
    path = root/"scripts"/"seed.sql"
    cfg  = load_db_config()
    conn =connect(cfg)
    run_sql_file(conn,path)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    migrations_dir = root / "migrations"
    #
    # seed_sql = root / "scripts" / "seed.sql"

    cfg = load_db_config()
    wait_for_db(cfg, timeout_s=60)
    migration_files = list_migration_files(migrations_dir)

    with connect(cfg) as conn:
        for path in migration_files:
            run_sql_file(conn, path)
        conn.commit()



if __name__ == "__main__":
    main()