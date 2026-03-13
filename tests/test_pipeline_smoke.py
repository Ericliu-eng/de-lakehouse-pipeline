from de_lakehouse_pipeline.cli import run_stock


def test_pipeline_smoke(tmp_path, monkeypatch):
    def fake_fetch(symbol="AAPL"):
        return {"mock": "data"}

    monkeypatch.setattr(
        "de_lakehouse_pipeline.cli.fetch_daily_stock",
        fake_fetch,
    )
    file_path = run_stock(tmp_path)

    assert file_path.exists()
    assert file_path.name == "stock.json"