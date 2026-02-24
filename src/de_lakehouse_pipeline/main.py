from __future__ import annotations

from pathlib import Path

import pandas as pd


def transform(df: pd.DataFrame) -> pd.DataFrame:
    df = df.dropna(subset=["name"])
    df = df[df["amount"] > 0]
    return df


#            "name": ["A", "B", None],
          #  "amount": [10, -5, 20],
def run_pipeline(input_path: Path, output_path: Path) -> pd.DataFrame:
    print("Starting pipeline...")

    # --- Extract ---
    if not input_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_path}. Create data/raw/sample.csv first."
        )

    df = pd.read_csv(input_path)
    print(f"Loaded {len(df)} rows from {input_path}")

    # --- Transform ---
    before = len(df)
    df2 = transform(df)
    after = len(df2)
    print(f"Transformed: {before} -> {after} rows")

    # --- Load ---
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df2.to_csv(output_path, index=False)
    print(f"Saved {len(df2)} rows to {output_path}")

    print("Pipeline finished successfully")
    return df2


def main() -> None:
    input_path = Path("data/raw/sample.csv")
    output_path = Path("data/processed/output.csv")
    run_pipeline(input_path=input_path, output_path=output_path)


if __name__ == "__main__":
    main()