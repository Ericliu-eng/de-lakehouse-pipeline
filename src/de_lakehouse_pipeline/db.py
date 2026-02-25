from __future__ import annotations

import os
import time

#dataclass:Used to define structured config objects
from dataclasses import dataclass
#PostgreSQL driver (connect Python ↔ Postgres)
import psycopg

#auto-generates __init__, __repr__, etc.and frozen = true ,makes it immutable
#数据库对象，用来统一存：host / port / dbname / user / password
@dataclass(frozen=True)
class DBConfig:
    host: str
    port: int
    dbname: str
    user: str
    password: str

#DBConfig is a structured configuration object used to store database connection information.

def load_db_config() -> DBConfig:
    return DBConfig(
        #如果没有用默认值 ，第二个值
#os.environ = a dictionary of environment variables for the current Python process
        host=os.environ.get("DB_HOST", "localhost"),
        port=int(os.environ.get("DB_PORT", "5432")),
        dbname=os.environ.get("DB_NAME", "lakehouse"),
        user=os.environ.get("DB_USER", "lakehouse"),
        password=os.environ.get("DB_PASSWORD", "lakehouse"),
    )

#Convert config → connection string (DSN)
def make_dsn(cfg: DBConfig) -> str:
    #Data Source Name
    return (
        f"host={cfg.host} port={cfg.port} dbname={cfg.dbname} "
        f"user={cfg.user} password={cfg.password}"
    )

#Flow:DBConfig → DSN → psycopg → connection
def connect(cfg: DBConfig) -> psycopg.Connection:
    return psycopg.connect(make_dsn(cfg))

#Wait until database is ready to accept connections
def wait_for_db(cfg: DBConfig, timeout_s: int = 60) -> None:
    """Wait until DB is accepting connections (useful in CI/local)."""
    start = time.time()
    last_err: Exception | None = None

    while time.time() - start < timeout_s:
        try:            #auto close connection
            with connect(cfg) as conn:
                        #Cursor = run SQL
                with conn.cursor() as cur:
                    #check DB is alive and responding
                    cur.execute("SELECT 1;")
                    cur.fetchone()
            return
        except Exception as e:
            last_err = e
            time.sleep(1)

    raise RuntimeError(f"DB not ready after {timeout_s}s. Last error: {last_err}")