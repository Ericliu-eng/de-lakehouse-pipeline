import argparse
from pathlib import Path
from datetime import date

from de_lakehouse_pipeline.ingest.market_data_client import fetch_daily_stock
#from de_lakehouse_pipeline.ingest.weather_client import fetch_current_weather
from de_lakehouse_pipeline.load.loader import load_raw_stock_json
from de_lakehouse_pipeline.transform.transform_stock import parse_alpha_vantage_daily
from de_lakehouse_pipeline.load.db.stock_writer import upsert_stock_prices
from de_lakehouse_pipeline.load.db.connection import load_db_config, wait_for_db, connect
from de_lakehouse_pipeline.load.metadata import record_load
from de_lakehouse_pipeline.load.db.metadata_writer import insert_load_metadata
from de_lakehouse_pipeline.ingest.io import save_raw_data

def today_time():
    return date.today().isoformat()

def run_stock(root:Path = None):
    print("Running daily pipeline...")
    #Step 1: ingest
    data = fetch_daily_stock("AAPL")
    
    file_path = save_raw_data(data,"stock",root)
    #read today json
    dict = load_raw_stock_json(file_path)
    #transform the dict readiable
    db_row = parse_alpha_vantage_daily(dict)
    #connect db
    cfg = load_db_config()
    wait_for_db(cfg, timeout_s=60)
    with connect(cfg) as conn:
        #write into db    
        print("write stock into db")
        upsert_stock_prices(conn,db_row)
        #record it 
        metadata_payload = record_load(
        source="alpha_vantage",
        load_date=today_time(),
        version=today_time(),
        record_count=len(db_row),
        )
        print("start record metadata to db ")
        insert_load_metadata(conn, metadata_payload)
        print("finish...")
    return file_path


    #return a multiply row which can write into the db
    #list_tuple = parse_alpha_vantage_daily(db_row)

 
    # upsert_stock_prices(list_tuple)
    # print(json.dumps(data, indent=2)[:1000])
    # print(f"Saved raw file to: {file_path}")
    # print("Step 2: load")
    # print("Step 3: transform")
    # return  file_path



def run_weather(city: str) -> None:
    #"Step 1: ingest"
    #data = fetch_current_weather(city)
    #file_path = save_raw_data(data,"weather")
    #"Step 2: load"
    #load_file = load_weather_file_to_db(file_path)
    print()

    #"Step 3: transform"
    #infor = trans_weather(load_file)
    #print(infor)


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
