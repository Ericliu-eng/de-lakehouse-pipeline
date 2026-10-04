"""
Minimal serving API for de-lakehouse-pipeline.
"""
from __future__ import annotations

import uvicorn
from pathlib import Path
from typing import Any
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from de_lakehouse_pipeline.load.db.connection import connect, load_db_config



BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI(title="DE Lakehouse Serving API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

def featch_latest_price() -> dict[str, Any] | None:
    sql = """SELECT symbol, latest_ts, close_price, volume
                FROM mart_symbol_latest_price
                ORDER BY latest_ts DESC
                LIMIT 1;"""
    with connect(load_db_config()) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            row = cur.fetchone()

    if row is None:
        return None

    return {
        "symbol": row[0],
        "latest_ts": row[1],
        "close_price": row[2],
        "volume": row[3],
    }

@app.get("/latest-price")
def latest_price() -> dict[str, Any]:
    row = featch_latest_price()
            
    if row is None:
        return {
            "symbol": None,
            "latest_ts": None,
            "close_price": None,
            "volume": None,
            "source": "database",
        }

    return {
        "symbol": row["symbol"],
        "latest_ts": row["latest_ts"],
        "close_price": row["close_price"],
        "volume": row["volume"],
        "source": "database",
    }

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request) -> HTMLResponse:
    data = latest_price()

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "title": "DE Lakehouse Dashboard",
            "latest_price": data,
        },
    )


def main() -> None:

    uvicorn.run("src.serve.api:app", host="127.0.0.1", port=8000, reload=True)


if __name__ == "__main__":
    main()
