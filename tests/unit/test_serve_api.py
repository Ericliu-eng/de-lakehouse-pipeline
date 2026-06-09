from fastapi.testclient import TestClient

from src.serve.api import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_latest_price() -> None:
    response = client.get("/latest-price")

    assert response.status_code == 200

    data = response.json()
    assert data["symbol"] == "AAPL"
    assert data["ts"] == "2026-06-22T00:00:00Z"
    assert data["close"] == 195.00
    assert data["source"] == "mock"


def test_dashboard_returns_html() -> None:
    response = client.get("/dashboard")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "DE Lakehouse Dashboard" in response.text
    assert "AAPL" in response.text    