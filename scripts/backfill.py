import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start")
    parser.add_argument("--end")
    args = parser.parse_args()

    print(f"Backfill from {args.start} to {args.end}")

if __name__ == "__main__":
    main()