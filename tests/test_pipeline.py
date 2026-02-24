import pandas as pd
import pytest

from de_lakehouse_pipeline.main import transform ,main

#normal case 
def test_transform_normal_case():
    df = pd.DataFrame(
        {
            "name": ["Alice", "Bob", "Cathy"],
            "amount": [10, 5, 1],
        }
    )
    out = transform(df)
    assert len(out) == 3
    assert (out["amount"] > 0).all()
    assert out["name"].notna().all()


def test_transform_drops_missing_name_and_nonpositive_amount():
    df = pd.DataFrame(
        {
            "name": ["Alice", None, "Bob", "Cathy"],
            "amount": [10, 5, 0, -3],
        }
    )
    out = transform(df)

    # Keep only rows where name is present AND amount > 0
    assert len(out) == 1
    assert out.iloc[0]["name"] == "Alice"
    assert out.iloc[0]["amount"] == 10


def test_main_raises_if_input_missing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(FileNotFoundError) as excinfo:
        main()
    print(str(excinfo.value))