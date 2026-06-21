import json
from pathlib import Path



def load_raw_stock_json(file_path:Path = None) -> dict:
    if file_path is None:
        raise FileNotFoundError(f"Raw file not found: {file_path}")
    # r  = read mode
    with open(file_path,"r") as f:
        data = json.load(f)
    return data