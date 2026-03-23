import logging
from pathlib import Path
# from src.utils.db import execute_sql_file
from de_lakehouse_pipeline.load.db.connection import connect,load_db_config
logger = logging.getLogger(__name__)

def run():

    root = Path(__file__).resolve().parents[4]
    sql_file_path = Path(root/"sql/marts/mart_symbol_volume_rank.sql")
    
    if not sql_file_path.exists():
        logger.error(f"SQL file not found at {sql_file_path}")
        return

    logger.info("Calculating Market Volume Ranks...")
    config =load_db_config()
    sql = sql_file_path.read_text(encoding="utf-8").strip()
        # 在大厂实践中，这里通常会有一个依赖检查：
    # 确保 Mart 1 (summary) 今天已经跑成功了，再跑 Mart 3
    try:
        with connect(config) as conn:
            with conn.cursor() as cur:
            # 执行 SQL 逻辑
            # db.execute(sql)
                cur.execute(sql)
                conn.commit()
        print("Mart 3: Successfully ranked symbols by volume.")
    except Exception as e:
        logger.error(f"Failed to calculate ranks: {e}")
        raise

if __name__ == "__main__":
    run()