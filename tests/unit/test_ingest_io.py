import json
from datetime import date
from pathlib import Path

from de_lakehouse_pipeline.ingest.io import save_raw_data


def test_save_raw_data(tmp_path: Path):
    data = {
        "Meta Data": {"2. Symbol": "AAPL"},
        "Time Series (Daily)": {
            "2026-06-15": {"1. open": "294.1200"}
        },
    }

    file_path = save_raw_data(
        data,
        "stock",
        root=tmp_path,
        run_date=date(2026, 6, 20),
    )

    assert file_path.exists()
    assert file_path == (
        tmp_path / "data" / "raw" / "2026-06-20" / "AAPL" / "stock.json"
    )
    assert json.loads(file_path.read_text()) == data