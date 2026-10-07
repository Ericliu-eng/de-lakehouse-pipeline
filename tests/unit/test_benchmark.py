from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import psycopg
import pytest

from de_lakehouse_pipeline import pipeline
from de_lakehouse_pipeline.metrics import PipelineMetric
from de_lakehouse_pipeline.observability.run_repository import PipelineRunHandle
from orchestration import dagster_pipeline as runner
from scripts import benchmark


def test_replay_runs_real_pipeline_with_symbol_and_isolated_raw_path(tmp_path):
    data = {"Meta Data": {"2. Symbol": "AAPL"}, "Time Series (Daily)": {}}
    with benchmark.replay({"AAPL": data}, tmp_path) as calls:
        result = pipeline.load_stock("AAPL")
    assert result.raw_path == tmp_path / "data" / "raw" / benchmark.date.today().isoformat() / "AAPL" / "stock.json"
    assert result.raw_path.exists()
    assert result.rows_received == 0
    assert calls["fetch"] == 1


def test_replay_never_reports_real_pipeguard_or_uploads_s3(monkeypatch, tmp_path):
    monkeypatch.setenv("PIPEGUARD_API_URL", "https://monitor.example")
    monkeypatch.setenv("PIPEGUARD_API_KEY", "fake-key")
    monkeypatch.setenv("ENABLE_S3_RAW_UPLOAD", "true")
    transport = Mock(side_effect=AssertionError("must not send simulated runs"))
    monkeypatch.setattr(runner, "report_run", transport)
    metric = PipelineMetric("benchmark", "2026-10-06T00:00:00+00:00")
    metric.finish("success")
    with benchmark.replay({}, tmp_path):
        assert benchmark.os.environ["ENABLE_S3_RAW_UPLOAD"] == "false"
        runner._report_to_pipeguard(PipelineRunHandle(1, uuid4()), metric, [])
    transport.assert_not_called()
    assert benchmark.os.environ["PIPEGUARD_API_KEY"] == "fake-key"
    assert benchmark.os.environ["ENABLE_S3_RAW_UPLOAD"] == "true"


class AdminConnection:
    def __init__(self, exists=False, create_error=None):
        self.exists = exists
        self.create_error = create_error
        self.statements = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, query, params=()):
        self.statements.append((query, params))
        if len(self.statements) == 1:
            return SimpleNamespace(fetchone=lambda: (1,) if self.exists else None)
        if self.create_error:
            raise self.create_error
        return SimpleNamespace(fetchone=lambda: None)


def admin(monkeypatch, connection):
    monkeypatch.setattr(benchmark, "load_db_config", lambda: SimpleNamespace(dbname="development"))
    monkeypatch.setattr(benchmark, "make_dsn", lambda cfg: "fake-dsn")
    monkeypatch.setattr(benchmark, "wait_for_db", lambda *args, **kwargs: None)
    monkeypatch.setattr(benchmark.psycopg, "connect", lambda *args, **kwargs: connection)


def test_existing_database_is_refused_without_create_or_drop(monkeypatch):
    conn = AdminConnection(exists=True)
    admin(monkeypatch, conn)
    cleanup = Mock()
    monkeypatch.setattr(benchmark, "drop_database", cleanup)
    with pytest.raises(SystemExit, match="existing database"):
        with benchmark.benchmark_database("valuable"):
            pytest.fail("must not enter benchmark")
    assert len(conn.statements) == 1
    assert conn.statements[0][1] == ("valuable",)
    cleanup.assert_not_called()


def test_concurrent_database_creation_failure_never_triggers_cleanup(monkeypatch):
    admin(monkeypatch, AdminConnection(create_error=psycopg.errors.DuplicateDatabase("already exists")))
    cleanup = Mock()
    monkeypatch.setattr(benchmark, "drop_database", cleanup)
    with pytest.raises(psycopg.errors.DuplicateDatabase):
        with benchmark.benchmark_database("valuable"):
            pytest.fail("must not enter benchmark")
    cleanup.assert_not_called()


def test_configured_database_is_refused_before_connection(monkeypatch):
    monkeypatch.setattr(benchmark, "load_db_config", lambda: SimpleNamespace(dbname="development"))
    connect = Mock()
    monkeypatch.setattr(benchmark.psycopg, "connect", connect)
    with pytest.raises(SystemExit, match="configured database"):
        benchmark.create_database("development")
    connect.assert_not_called()


@pytest.mark.parametrize("name", ["", "x" * 64, "库" * 22])
def test_database_name_cannot_be_silently_truncated(monkeypatch, name):
    connect = Mock()
    monkeypatch.setattr(benchmark.psycopg, "connect", connect)
    with pytest.raises(SystemExit, match="63 UTF-8 bytes"):
        benchmark.create_database(name)
    connect.assert_not_called()


@pytest.mark.parametrize("keep", [False, True])
def test_owned_database_cleanup_and_environment_restore_after_failure(monkeypatch, keep):
    admin(monkeypatch, AdminConnection())
    monkeypatch.setenv("DB_NAME", "development")
    cleanup = Mock()
    monkeypatch.setattr(benchmark, "drop_database", cleanup)
    with pytest.raises(RuntimeError, match="injected"):
        with benchmark.benchmark_database("new_benchmark", keep=keep):
            assert benchmark.os.environ["DB_NAME"] == "new_benchmark"
            raise RuntimeError("injected")
    assert benchmark.os.environ["DB_NAME"] == "development"
    if keep:
        cleanup.assert_not_called()
    else:
        cleanup.assert_called_once_with("new_benchmark")


def test_replay_preserves_explicit_historical_partition(tmp_path):
    with benchmark.replay({}, tmp_path):
        path = pipeline.save_raw_data([], "tiingo", run_date=benchmark.date(2000, 1, 3), symbol="MSFT")
    assert path == Path(tmp_path) / "data" / "raw" / "2000-01-03" / "MSFT" / "tiingo.json"
