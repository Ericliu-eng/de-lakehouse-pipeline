import logging
from pathlib import Path
# from src.utils.db import get_connection
from de_lakehouse_pipeline.load.db.connection import connect,load_db_config

logger = logging.getLogger(__name__)

def run():

    
    root = Path(__file__).resolve().parents[4]
    sql_file_path = Path(root/"sql/marts/mart_symbol_latest_price.sql")
    
    if not sql_file_path.exists():
        logger.error(f"SQL file not found at {sql_file_path}")
        return

    logger.info("Updating Latest Price Mart...")
    config =load_db_config()
    sql = sql_file_path.read_text(encoding="utf-8").strip()
    with connect(config) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            conn.commit()
    
    print("Mart 2: Successfully updated latest snapshots for all symbols.")

if __name__ == "__main__":
    run()