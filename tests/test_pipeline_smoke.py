from de_lakehouse_pipeline.cli import run_daily

def test_pipeline_smoke(tmp_path, monkeypatch):
    # fake API response
    def fake_fetch(symbol="AAPL"):
        return {"mock": "data"}

    monkeypatch.setattr(
        "de_lakehouse_pipeline.ingest.alpha_vantage_client.fetch_daily_stock",
        fake_fetch,
    )

    raw_dir = run_daily(tmp_path)

    files = list(raw_dir.glob("*/stock.json"))
    assert len(files) > 0