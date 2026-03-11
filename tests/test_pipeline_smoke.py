from pathlib import Path
from de_lakehouse_pipeline.cli import run_daily


def test_pipeline_smoke(tmp_path):
    """
    Smoke test: verify the pipeline runs end-to-end
    and writes a raw JSON file.
    """
    # run pipeline using temporary directory
    
    raw_dir = run_daily(tmp_path)
    files = list(raw_dir.glob("*/stock.json"))
    assert len(files) > 0
