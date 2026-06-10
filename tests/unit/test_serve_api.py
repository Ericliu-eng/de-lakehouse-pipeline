from fastapi.testclient import TestClient

from src.serve.api import app
import src.serve.api as api

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_latest_price(monkeypatch) -> None:
    def mock_latest_price():
        return {
            "symbol": "AAPL",
            "latest_ts": "2026-06-22T00:00:00Z",
            "close_price": 195.00,
            "volume": 1000000,
        }

    monkeypatch.setattr(api, "featch_latest_price", mock_latest_price)

    response = client.get("/latest-price")

    assert response.status_code == 200

    data = response.json()
    assert data["symbol"] == "AAPL"
    assert data["latest_ts"] == "2026-06-22T00:00:00Z"
    assert data["close_price"] == 195.00
    assert data["volume"] == 1000000
    assert data["source"] == "database"

def test_dashboard_returns_html() -> None:
    response = client.get("/dashboard")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "DE Lakehouse Dashboard" in response.text
    assert "AAPL" in response.text    