import pytest

from de_lakehouse_pipeline.observability.pipeguard_reporter import (
    API_KEY_ENV,
    TIMEOUT_ENV,
    URL_ENV,
)


@pytest.fixture(autouse=True)
def _no_pipeguard_reporting(monkeypatch):
    """Keep every test from reporting to a real PipeGuard.

    Importing the market-data client runs load_dotenv(), so a developer who puts
    PipeGuard credentials in .env would otherwise have the test suite post runs
    to the live service. Tests that exercise reporting pass an explicit config
    and a fake session instead.
    """
    for name in (URL_ENV, API_KEY_ENV, TIMEOUT_ENV):
        monkeypatch.delenv(name, raising=False)
