
from de_lakehouse_pipeline.cli import run_stock

def test_incremental_behavior():
    run_stock()
    run_stock()
