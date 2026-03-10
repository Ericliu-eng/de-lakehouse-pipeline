from pathlib import Path
from datetime import date
import argparse
import json

def root() -> Path:
    return  Path(__file__).resolve().parents[3]
    
    


def trans_weather():
    today = date.today().isoformat()
    root_ = root()
    root_path = root_ / "data"/ "raw"/f"{today}"/"weather.json"
    print(root_path)
    with open(root_path) as f:
        data = json.load(f)
    print(data)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command")
    args = parser.parse_args()

    if args.command == "trans_weather":
        trans_weather()






if __name__ == "__main__":
    main()
