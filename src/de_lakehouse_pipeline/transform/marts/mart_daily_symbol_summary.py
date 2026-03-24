import logging
from pathlib import Path
from de_lakehouse_pipeline.load.db.connection import load_db_config, connect

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_daily_summary(conn=None):
    root = Path(__file__).resolve().parents[4]
    sql_file_path = root / "sql/marts/mart_daily_symbol_summary.sql"

    if not sql_file_path.exists():
        logger.error(f"SQL file not found at {sql_file_path}")
        return

    sql = sql_file_path.read_text(encoding="utf-8").strip()
    logger.info("Starting Mart 1: mart_daily_symbol_summary transformation...")

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

        logger.info("Successfully populated mart_daily_symbol_summary table.")
    except Exception as e:
        logger.error(f"Transformation failed: {e}")
        raise


if __name__ == "__main__":
    run_daily_summary()