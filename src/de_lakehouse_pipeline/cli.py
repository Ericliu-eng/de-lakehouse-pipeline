import argparse
import json
from pathlib import Path
from datetime import date

from de_lakehouse_pipeline.ingest.alpha_vantage_client import fetch_daily_stock
from de_lakehouse_pipeline.ingest.weather_client import fetch_current_weather

def project_root() -> Path:

    return Path(__file__).resolve().parents[2]

def save_raw_data(data, source, root: Path):

    today = date.today().isoformat()
    raw_dir = root / "raw" / today
    raw_dir.mkdir(parents=True, exist_ok=True)

    file_path = raw_dir / f"{source}.json"

    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)

    return file_path

def run_daily() -> None:
    print("Running daily pipeline...")
    print("Step 1: ingest")
    data = fetch_daily_stock("AAPL")
    file_path = save_raw_data(data,"stock",Path("data"))
    print(json.dumps(data, indent=2)[:1000])
    print(f"Saved raw file to: {file_path}")
    print("Step 2: load")
    print("Step 3: transform")


def run_weather(city: str) -> None:
    print("Running weather pipeline...")
    print("Step 1: ingest")
    data = fetch_current_weather(city)
    file_path = save_raw_data(data,"weather",Path("data"))
    print(json.dumps(data, indent=2)[:1000])
    print(f"Saved raw file to: {file_path}")
    print("Step 2: load")
    print("Step 3: transform")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["run_daily", "run_weather"])
    parser.add_argument("--city", default="Berkeley,US")
    args = parser.parse_args()

    if args.command == "run_daily":
        run_daily()
    elif args.command == "run_weather":
        run_weather(args.city)


if __name__ == "__main__":
    main()
