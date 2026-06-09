"""
Smoke tests for the serving layer and dashboard 

These tests should stay dependency-light and should not require a real database
or external API.
"""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from src.serve.api import app

client = TestClient(app)

@pytest.mark.smoke
def test_health_endpoint_returns_ok() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@pytest.mark.smoke
def test_latest_price_endpoint_returns_expected_shape() -> None:
    response = client.get("/latest-price")

    assert response.status_code == 200

    data = response.json()
    """"symbol": "AAPL",
        "ts": "2026-06-22T00:00:00Z",
        "close": 195.00,
        "source": "mock",
    """
    assert "symbol" in data
    assert "ts" in data
    assert "close" in data
    assert "source" in data

    assert isinstance(data["symbol"], str)
    assert isinstance(data["ts"], str)
    assert isinstance(data["close"], int | float)
    assert isinstance(data["source"], str)

@pytest.mark.smoke
def test_dashboard_app_file_exists() -> None:
    dashboard_path = Path("src/serve/templates/dashboard.html")

    assert dashboard_path.exists()
    assert dashboard_path.is_file()

@pytest.mark.smoke
def test_dashboard_app_contains_expected_title() -> None:
    dashboard_path = Path("src/serve/templates/dashboard.html")
    content = dashboard_path.read_text(encoding="utf-8")

    assert "Dashboard" in content