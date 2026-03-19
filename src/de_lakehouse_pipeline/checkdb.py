import tkinter as tk
import pandas as pd

from pandastable import Table
from de_lakehouse_pipeline.load.db.connection import connect,load_db_config,wait_for_db

def view_market_bars():
    cfg = load_db_config()
    wait_for_db(cfg, timeout_s=60)
    with connect(cfg) as conn:
        df = pd.read_sql(
        """
        SELECT *
        FROM load_metadata
        ORDER BY ts DESC
        """,
        conn
    )

    root = tk.Tk()
    root.title("market_bars")

    frame = tk.Frame(root)
    frame.pack(fill="both", expand=True)

    table = Table(frame, dataframe=df, showtoolbar=True, showstatusbar=True)
    table.show()

    root.mainloop()


if __name__ == "__main__":
    view_market_bars()