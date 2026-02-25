from __future__ import annotations

import pytest

from de_lakehouse_pipeline.db import DBConfig, load_db_config, make_dsn, wait_for_db


#Unit Test 1 — defaults load correctly
#MonkeyPatch
#Temporarily modify the environment (e.g., env), and automatically restore it after testing.
def test_load_db_config_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
# Delete DB_HOST.  raising=False If this variable doesn't exist, don't report an error.   
    monkeypatch.delenv("DB_HOST", raising=False)
    monkeypatch.delenv("DB_PORT", raising=False)
    monkeypatch.delenv("DB_NAME", raising=False)
    monkeypatch.delenv("DB_USER", raising=False)
    monkeypatch.delenv("DB_PASSWORD", raising=False)

    cfg = load_db_config()

    assert cfg.host == "localhost"
    assert cfg.port == 5432
    assert cfg.dbname == "lakehouse"
    assert cfg.user == "lakehouse"
    assert cfg.password == "lakehouse"

#Unit Test 2 — env overrides work
#When environment variables exist, do they correctly override default values?
def test_load_db_config_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DB_HOST", "db")
    monkeypatch.setenv("DB_PORT", "6543")
    monkeypatch.setenv("DB_NAME", "testdb")
    monkeypatch.setenv("DB_USER", "u")
    monkeypatch.setenv("DB_PASSWORD", "p")

    cfg = load_db_config()

    assert cfg.host == "db"
    assert cfg.port == 6543
    assert cfg.dbname == "testdb"
    assert cfg.user == "u"
    assert cfg.password == "p"
# Unit Test 3 — DSN formatting is correct
def test_make_dsn_contains_expected_fields() -> None:
#f embeds variables directly into the string.
    cfg = DBConfig(host="db", port=5432, dbname="lakehouse", user="lakehouse", password="lakehouse") 
    dsn = make_dsn(cfg)

    assert "host=db" in dsn
    assert "port=5432" in dsn
    assert "dbname=lakehouse" in dsn
    assert "user=lakehouse" in dsn
    assert "password=lakehouse" in dsn

# edge/failure test
def test_wait_for_db_times_out_fast_on_bad_port() -> None:
# deterministic: local unused port should refuse immediately; timeout keeps it bounded
    cfg = DBConfig(host="127.0.0.1", port=65432, dbname="x", user="x", password="x")
    #Assert that the code will throw an exception(pytest.raises（error）) if raise a error passed 
    with pytest.raises(Exception):
        wait_for_db(cfg, timeout_s=1)
