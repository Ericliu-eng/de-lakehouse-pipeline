

from de_lakehouse_pipeline.load.loader import load_raw_stock_json

#unit test 
def test_load_raw_stock_json_success(tmp_path):
    file = tmp_path / "sample.json"
    file.write_text('{"symbol": "AAPL"}')
    result = load_raw_stock_json(file)
    assert result == {"symbol": "AAPL"}