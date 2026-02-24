from __future__ import annotations

from pathlib import Path

import pandas as pd

from de_lakehouse_pipeline.main  import run_pipeline


def test_smoke_pipeline(tmp_path: Path) -> None:
    # Arrange: create fake raw data
    input_path = tmp_path / "sample.csv"
    output_path = tmp_path / "output.csv"

    df = pd.DataFrame(
        {
            "name": ["A", "B", None],
            "amount": [10, -5, 20],
        }
    )
    df.to_csv(input_path, index=False)

    # Act
    result = run_pipeline(input_path=input_path, output_path=output_path)

    # Assert: output exists + behavior is correct
    assert output_path.exists()

    out_df = pd.read_csv(output_path)
    assert len(out_df) == 1
    assert out_df.iloc[0]["name"] == "A"
    assert out_df.iloc[0]["amount"] == 10

    # extra: returned df matches saved df
    assert len(result) == 1