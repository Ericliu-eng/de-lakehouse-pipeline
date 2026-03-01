from __future__ import annotations

from pathlib import Path

from de_lakehouse_pipeline.db import load_db_config, wait_for_db, connect


def run_sql_file(conn, path: Path) -> None:
    """
    Run a single .sql file against the database using an existing connection.
    Keeping one connection avoids reconnecting per file and makes the migration
    feel transactional/consistent.
    """
    sql = path.read_text(encoding="utf-8").strip()
    if not sql:
        return  # ignore empty files safely

    with conn.cursor() as cur:
        cur.execute(sql)


def list_migration_files(migrations_dir: Path):
    return sorted(migrations_dir.glob("*.sql"))


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    migrations_dir = root / "migrations"
    seed_sql = root / "scripts" / "seed.sql"

    cfg = load_db_config()
    wait_for_db(cfg, timeout_s=60)

    migration_files = list_migration_files(migrations_dir)

    print("Running migrations...")
    with connect(cfg) as conn:
        for path in migration_files:
            run_sql_file(conn, path)
            print(f"Applied: {path.relative_to(root)}")

        # Seed should come last (optional but typical).
        if seed_sql.exists():
            print("Seeding data...")
            run_sql_file(conn, seed_sql)
            print(f"Applied: {seed_sql.relative_to(root)}")

        conn.commit()
    print("Done.")



if __name__ == "__main__":
    main()