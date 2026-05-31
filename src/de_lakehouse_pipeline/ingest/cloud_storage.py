from __future__ import annotations

import json
import os
from datetime import date
from typing import Any, Mapping


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


def upload_raw_payload_if_enabled(
    payload: dict,
    source: str,
    symbol: str,
    run_date: date,
    filename: str,
    s3_client: Any | None = None,
    env: Mapping[str, str] | None = None,
) -> str | None:
    env_values = os.environ if env is None else env

    upload_enabled = env_values.get("ENABLE_S3_RAW_UPLOAD", "").lower() == "true"
    if not upload_enabled:
        return None

    bucket = env_values.get("S3_RAW_BUCKET")
    if not bucket:
        raise ValueError("S3_RAW_BUCKET is required when S3 upload is enabled")

    key = build_raw_object_key(
        source=source,
        symbol=symbol,
        run_date=run_date,
        filename=filename,
    )

    client = s3_client or _build_s3_client()
    client.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(payload, indent=2).encode("utf-8"),
        ContentType="application/json",
    )

    return f"s3://{bucket}/{key}"


def _build_s3_client() -> Any:
    import boto3

    return boto3.client("s3")