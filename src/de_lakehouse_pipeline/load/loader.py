import json
from pathlib import Path
from datetime import date


def project_root():
    return Path(__file__).resolve().parents[3]

def load_raw_file(file_path:Path = None,source:str = ""):
    today = date.today().isoformat()
    root = project_root()

    if file_path is None:
        raise FileNotFoundError(f"Raw file not found: {file_path}")
    with open(file_path,"r") as f:
        data = json.load(f)
    return data
