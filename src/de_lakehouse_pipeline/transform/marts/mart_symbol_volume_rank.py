import logging
from pathlib import Path
from de_lakehouse_pipeline.load.db.connection import connect, load_db_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_symbol_volume(conn=None):
    root = Path(__file__).resolve().parents[4]
    sql_file_path = root / "sql/marts/mart_symbol_volume_rank.sql"

    if not sql_file_path.exists():
        logger.error(f"SQL file not found at {sql_file_path}")
        return

    logger.info("Calculating Market Volume Ranks...")
    sql = sql_file_path.read_text(encoding="utf-8").strip()

    if conn is not None:
        with conn.cursor() as cur:
            cur.execute(sql)
        return

    config = load_db_config()
    try:
        with connect(config) as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()
        logger.info("Mart 3: Successfully ranked symbols by volume.")
    except Exception as e:
        logger.error(f"Failed to calculate ranks: {e}")
        raise


if __name__ == "__main__":
    run_symbol_volume()