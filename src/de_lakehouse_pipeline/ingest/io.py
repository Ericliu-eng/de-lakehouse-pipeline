from pathlib import Path
from datetime import date
import json

def project_root() -> Path:

    return Path(__file__).resolve().parents[3]

def today_time():
    return date.today()

def save_raw_data(data:dict,name:str, root:Path = None,run_date: date = None):
    symbol = data["Meta Data"]["2. Symbol"]
    #symbol = data.symbol
    if root is None:
        root  = project_root()
    partition_date = run_date  or  today_time()
    raw_dir = (
    root
    / "data"
    / "raw"
    / partition_date.isoformat()
    / symbol)
    raw_dir.mkdir(parents=True, exist_ok=True)

    file_path = raw_dir / f"{name}.json"

    with open(file_path, "w") as f:
        #把 data 写进文件 f 里面。
        json.dump(data, f, indent=2)

    return file_path