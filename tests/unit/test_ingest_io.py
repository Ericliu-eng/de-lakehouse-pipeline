from datetime import date
from pathlib import Path
from de_lakehouse_pipeline.ingest.io import save_raw_data


#unit test 1 能否创建 data/raw/YYYY-MM-DD/能否把 JSON 写进去/返回的 file path 是否正确
# tmp_path 临时文件夹
def test_save_raw_data(tmp_path: Path):
    data = {
        "Meta Data": {"2. Symbol": "AAPL"},
        "Time Series (Daily)": {},
    }
    file_path = save_raw_data(
        data,
        "stock",
        root=tmp_path,
        run_date=date(2026, 6, 20),
    )
    assert file_path.exists()
    assert file_path.suffix == ".json"
    assert file_path == tmp_path / "data" / "raw" / "2026-06-20" / "AAPL" / "stock.json"
