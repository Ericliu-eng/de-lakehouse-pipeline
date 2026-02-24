from __future__ import annotations

import os
import time
from dataclasses import dataclass

import psycopg


@dataclass(frozen=True)
class DBConfig:
    host: str
    port: int
    dbname: str
    user: str
    password: str


def load_db_config() -> DBConfig:
    return DBConfig(
        host=os.environ.get("DB_HOST", "localhost"),
        port=int(os.environ.get("DB_PORT", "5432")),
        dbname=os.environ.get("DB_NAME", "lakehouse"),
        user=os.environ.get("DB_USER", "lakehouse"),
        password=os.environ.get("DB_PASSWORD", "lakehouse"),
    )


def make_dsn(cfg: DBConfig) -> str:
    return (
        f"host={cfg.host} port={cfg.port} dbname={cfg.dbname} "
        f"user={cfg.user} password={cfg.password}"
    )


def connect(cfg: DBConfig) -> psycopg.Connection:
    return psycopg.connect(make_dsn(cfg))


def wait_for_db(cfg: DBConfig, timeout_s: int = 60) -> None:
    """Wait until DB is accepting connections (useful in CI/local)."""
    start = time.time()
    last_err: Exception | None = None

    while time.time() - start < timeout_s:
        try:
            with connect(cfg) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1;")
                    cur.fetchone()
            return
        except Exception as e:
            last_err = e
            time.sleep(1)

    raise RuntimeError(f"DB not ready after {timeout_s}s. Last error: {last_err}")