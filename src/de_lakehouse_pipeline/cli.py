import argparse
import json
from pathlib import Path
from datetime import date

from de_lakehouse_pipeline.ingest.alpha_vantage_client import fetch_daily_stock
from de_lakehouse_pipeline.ingest.weather_client import fetch_current_weather
from de_lakehouse_pipeline.load.loader import load_raw_file
from de_lakehouse_pipeline.transform.transform_weather import trans_weather
from de_lakehouse_pipeline.load.metadata import record_load

def project_root() -> Path:

    return Path(__file__).resolve().parents[2]
def today_time():
    return date.today().isoformat()

def save_raw_data(data, source, root:Path = None):
    if root is None:
        root  = project_root()
    print("print root =================")
    print(root)
    today = today_time()
    raw_dir = root /"data"/ "raw" / today
    raw_dir.mkdir(parents=True, exist_ok=True)

    file_path = raw_dir / f"{source}.json"
    print(file_path)
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)

    return file_path

def run_stock(root:Path = None):
    print("Running daily pipeline...")
    print("Step 1: ingest")
    data = fetch_daily_stock("AAPL")
    file_path = save_raw_data(data,"stock",root)
    print(json.dumps(data, indent=2)[:1000])
    print(f"Saved raw file to: {file_path}")
    print("Step 2: load")
    print("Step 3: transform")
    return  file_path



def run_weather(city: str) -> None:
    print("Running weather pipeline...")
    print("Step 1: ingest")
    data = fetch_current_weather(city)
    file_path = save_raw_data(data,"weather")
    #print(json.dumps(data, indent=2)[:1000])
    print(f"Saved raw file to: {file_path}")
    print("Step 2: load")
    load_file = load_raw_file(source="weather")
    #def record_load(source: str, load_date: str, version: str, record_count: int):
    record_load("weather",today_time(),"1","1")
    print("Step 3: transform")
    infor = trans_weather(load_file)
    print(infor)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["run_stock", "run_weather"])
    parser.add_argument("--city", default="Berkeley,US")
    args = parser.parse_args()

    if args.command == "run_stock":
        run_stock()
    elif args.command == "run_weather":
        run_weather(args.city)


if __name__ == "__main__":
    main()
