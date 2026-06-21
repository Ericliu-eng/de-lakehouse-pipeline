
from de_lakehouse_pipeline.ingest.io import save_raw_data
import json

#unit test 1 能否创建 data/raw/YYYY-MM-DD/能否把 JSON 写进去/返回的 file path 是否正确
# tmp_path 临时文件夹
def test_save_raw_data(tmp_path):
    data = {
        "Meta Data": {
            "2. Symbol": "AAPL"
        },
        "Time Series (Daily)": {
            "2026-06-15": {
                "1. open": "294.1200"
            }
        }
    }
    file_path = save_raw_data(
        data,
        "stock",
        root=tmp_path
    )

    assert file_path.exists()
    assert file_path.suffix == ".json"
    assert file_path.name == "stock.json"

    saved_data = json.loads(file_path.read_text())

    assert saved_data == data