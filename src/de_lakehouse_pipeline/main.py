from __future__ import annotations

from pathlib import Path

import pandas as pd


def main() -> None:
    print("Starting pipeline...")

    # Paths (relative to repo root)
    input_path = Path("data/raw/sample.csv")
    output_path = Path("data/processed/output.csv")

    # --- Extract ---
    if not input_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_path}. Create data/raw/sample.csv first."
        )

    df = pd.read_csv(input_path)
    print(f"Loaded {len(df)} rows from {input_path}")

    # --- Transform (minimal + visible) ---
    # 1) Drop rows where name is missing
    before = len(df)
    df = df.dropna(subset=["name"])
    after = len(df)
    print(f"Dropped {before - after} rows with missing name")

    # 2) Keep only positive amount
    before = len(df)
    df = df[df["amount"] > 0]
    after = len(df)
    print(f"Filtered out {before - after} rows where amount <= 0")

    # --- Load ---
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Saved {len(df)} rows to {output_path}")

    print("Pipeline finished successfully")


if __name__ == "__main__":
    main()