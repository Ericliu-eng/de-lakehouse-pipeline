import argparse
import json


from de_lakehouse_pipeline.ingest.alpha_vantage_client import fetch_daily_stock
from de_lakehouse_pipeline.ingest.weather_client import fetch_current_weather


def run_daily() -> None:
    print("Running daily pipeline...")
    print("Step 1: ingest")
    data = fetch_daily_stock("AAPL")
    print(json.dumps(data, indent=2)[:1000])
    print("Step 2: load")
    print("Step 3: transform")


def run_weather(city: str) -> None:
    print("Running weather pipeline...")
    print("Step 1: ingest")
    data = fetch_current_weather(city)
    print(json.dumps(data, indent=2)[:1000])
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
