import pytest
from pathlib import Path
from de_lakehouse_pipeline.cli import save_raw_data
from de_lakehouse_pipeline.ingest.weather_client import fetch_current_weather

#unit test 1 能否创建 data/raw/YYYY-MM-DD/能否把 JSON 写进去/返回的 file path 是否正确
# tmp_path 临时文件夹
def test_save_raw_data():
    data = {"temp": 20}
    test_root = Path("data/test") 
    file_path = save_raw_data(
        data,
        "weather",
        root=test_root
    )

    assert file_path.exists()
    assert file_path.suffix == ".json"
    
#edge test
def test_fetch_current_weather_raises_when_api_key_missing(monkeypatch) -> None:
    # 删除环境变量
    monkeypatch.delenv("OPENWEATHER_API_KEY", raising=False)
    # 验证是否抛出异常
    with pytest.raises(ValueError):
         fetch_current_weather("Berkeley,US")

