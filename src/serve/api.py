"""
Minimal serving API for de-lakehouse-pipeline.
"""
from __future__ import annotations

import uvicorn
from pathlib import Path
#表示你后面可以用 Any 做类型标注：
from typing import Any
#从 FastAPI 库里导入 FastAPI 类。 创建 API 应用。
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
"""
导入 Uvicorn 服务器。
它负责：
运行 FastAPI
监听端口
接收请求
返回响应"""



BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI(title="DE Lakehouse Serving API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/latest-price")
def latest_price() -> dict[str, Any]:
    return {
        "symbol": "AAPL",
        "ts": "2026-06-22T00:00:00Z",
        "close": 195.00,
        "source": "mock",
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