from pathlib import Path
from datetime import date
import json

def project_root() -> Path:

    return Path(__file__).resolve().parents[2]

def today_time():
    return date.today().isoformat()

def save_raw_data(data, source, root:Path = None):
    if root is None:
        root  = project_root()
    today = today_time()
    raw_dir = root /"data"/ "raw" / today
    raw_dir.mkdir(parents=True, exist_ok=True)

    file_path = raw_dir / f"{source}.json"

    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)

    return file_path