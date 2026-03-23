
import logging
from pathlib import Path
# 假设你有一个基础的 DB 工具类，如果没有，可以用 psycopg2 或 sqlalchemy
# from src.utils.db import get_db_connection 
from de_lakehouse_pipeline.load.db.connection import load_db_config, connect
#de_lakehouse_pipeline.transform.marts.mart_daily_symbol_summary run_transform
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run():
    """
    执行 Mart 1: Daily Symbol Summary 的转换逻辑
    """
    # 1. 定位 SQL 文件位置 (相对于项目根目录)
    root = Path(__file__).resolve().parents[4]
    sql_file_path = Path(root/"sql/marts/mart_daily_symbol_summary.sql")
    
    if not sql_file_path.exists():
        logger.error(f"SQL file not found at {sql_file_path}")
        return

    # 2. 读取 SQL 内容
    # with open(sql_file_path, "r") as f:
    #     sql_query = f.read()
    sql = sql_file_path.read_text(encoding="utf-8").strip()

    logger.info("Starting Mart 1: mart_daily_symbol_summary transformation...")
    config = load_db_config()
    try:
        # 3. 执行 SQL (这里替换为你自己的数据库执行逻辑)
        with connect(config) as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
                conn.commit()
        
        # 模拟执行输出
        print(f"Executing SQL from {sql_file_path}...")
        logger.info("Successfully populated mart_daily_symbol_summary table.")
        
    except Exception as e:
        logger.error(f"Transformation failed: {e}")
        raise

if __name__ == "__main__":
    run()
