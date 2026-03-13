import json
from pathlib import Path




def project_root():
    return Path(__file__).resolve().parents[3]

def load_stock_file(file_path:Path = None) -> dict:
    if file_path is None:
        raise FileNotFoundError(f"Raw file not found: {file_path}")
    with open(file_path,"r") as f:
        data = json.load(f)
    return data

# def load_weather_json(file_path:Path = None):
#     if file_path is None:
#         raise FileNotFoundError(f"Raw file not found: {file_path}")
#     with open(file_path,"r") as f:
#         data = json.load(f)
#     return data
#load the stock price to db
