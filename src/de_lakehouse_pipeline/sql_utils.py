from pathlib import Path



def project_root() -> Path:

    return Path(__file__).resolve().parents[2]

def _read_sql(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()

    
def split_sql_statements(sqls: str) -> list[str]:
    return [sql.strip() for sql in sqls.split(";") if sql.strip()]
