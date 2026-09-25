from datetime import date

import pytest

from de_lakehouse_pipeline import cli


class FakeConnection:
    def __init__(self, events):
        self.events = events

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def commit(self):
        self.events.append("commit")


@pytest.fixture
def calls(monkeypatch):
    recorded = []
    monkeypatch.setattr(cli, "configure_logging", lambda: None)
    monkeypatch.setattr(cli, "run_stock", lambda symbol: recorded.append(("run_stock", symbol)))
    monkeypatch.setattr(cli, "run_marts", lambda: recorded.append(("run_marts",)))
    monkeypatch.setattr(
        cli,
        "run_backfill",
        lambda start, end, symbol: recorded.append(("backfill", start, end, symbol)),
    )
    return recorded


def run_cli(monkeypatch, *args):
    monkeypatch.setattr("sys.argv", ["cli", *args])
    cli.main()


def test_run_stock_command_passes_symbol(monkeypatch, calls):
    run_cli(monkeypatch, "run_stock", "--symbol", "MSFT")

    assert calls == [("run_stock", "MSFT")]


def test_run_stock_command_defaults_to_aapl(monkeypatch, calls):
    run_cli(monkeypatch, "run_stock")

    assert calls == [("run_stock", "AAPL")]


def test_run_marts_command(monkeypatch, calls):
    run_cli(monkeypatch, "run_marts")

    assert calls == [("run_marts",)]


def test_backfill_command_parses_date_range(monkeypatch, calls):
    run_cli(monkeypatch, "backfill", "--start", "2026-09-14", "--end", "2026-09-18", "--symbol", "NVDA")

    assert calls == [("backfill", date(2026, 9, 14), date(2026, 9, 18), "NVDA")]


@pytest.mark.parametrize(
    ("args", "message"),
    [
        (["--start", "2026-09-14"], "requires --start and --end"),
        (["--end", "2026-09-18"], "requires --start and --end"),
        (["--start", "2026-09-18", "--end", "2026-09-14"], "start date must be on or before end date"),
    ],
)
def test_backfill_command_rejects_invalid_ranges(monkeypatch, calls, args, message):
    with pytest.raises(ValueError, match=message):
        run_cli(monkeypatch, "backfill", *args)

    assert calls == []


def test_unknown_command_exits_with_usage_error(monkeypatch, calls):
    with pytest.raises(SystemExit) as exc_info:
        run_cli(monkeypatch, "drop_tables")

    assert exc_info.value.code == 2
    assert calls == []


def test_run_marts_builds_all_marts_in_one_transaction(monkeypatch):
    events = []
    monkeypatch.setattr(cli, "load_db_config", lambda: "cfg")
    monkeypatch.setattr(cli, "wait_for_db", lambda cfg, timeout_s: events.append("wait"))
    monkeypatch.setattr(cli, "connect", lambda cfg: FakeConnection(events))
    for name in ["run_daily_summary", "run_latest_price", "run_symbol_volume"]:
        monkeypatch.setattr(cli, name, lambda conn, name=name: events.append(name))

    cli.run_marts()

    assert events == ["wait", "run_daily_summary", "run_latest_price", "run_symbol_volume", "commit"]
