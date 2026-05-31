from __future__ import annotations

from datetime import date
from typing import Any


def build_raw_object_key(
    source: str,
    symbol: str,
    run_date: date,
    filename: str,
) -> str:
    clean_source = source.strip()
    clean_symbol = symbol.strip().upper()
    clean_filename = filename.strip()

    if not clean_source:
        raise ValueError("source is required")

    if not clean_symbol:
        raise ValueError("symbol is required")

    if not clean_filename:
        raise ValueError("filename is required")

    if "/" in clean_filename:
        raise ValueError("filename must not include directories")

    return (
        f"raw/{clean_source}/"
        f"symbol={clean_symbol}/"
        f"date={run_date.isoformat()}/"
        f"{clean_filename}"
    )


def _build_s3_client() -> Any:
    import boto3

    return boto3.client("s3")
