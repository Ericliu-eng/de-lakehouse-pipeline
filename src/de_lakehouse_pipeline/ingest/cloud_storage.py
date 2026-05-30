from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import date
from typing import Any, Mapping


ENABLE_S3_RAW_UPLOAD_ENV = "ENABLE_S3_RAW_UPLOAD"
S3_RAW_BUCKET_ENV = "S3_RAW_BUCKET"


@dataclass(frozen=True)
class S3RawLocation:
    bucket: str
    key: str

    @property
    def uri(self) -> str:
        return f"s3://{self.bucket}/{self.key}"


def build_raw_object_key(
    source: str,
    symbol: str,
    run_date: date,
    filename: str,
) -> str:
    clean_source = _clean_path_part(source, "source")
    clean_symbol = _clean_path_part(symbol.upper(), "symbol")
    clean_filename = _clean_filename(filename)

    return (
        f"raw/{clean_source}/"
        f"symbol={clean_symbol}/"
        f"date={run_date.isoformat()}/"
        f"{clean_filename}"
    )


def build_s3_raw_location(
    bucket: str,
    source: str,
    symbol: str,
    run_date: date,
    filename: str,
) -> S3RawLocation:
    clean_bucket = _clean_bucket(bucket)
    key = build_raw_object_key(source, symbol, run_date, filename)
    return S3RawLocation(bucket=clean_bucket, key=key)


def upload_json_to_s3(
    s3_client: Any,
    bucket: str,
    key: str,
    payload: dict,
) -> S3RawLocation:
    clean_bucket = _clean_bucket(bucket)
    clean_key = _clean_s3_key(key)
    body = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")

    s3_client.put_object(
        Bucket=clean_bucket,
        Key=clean_key,
        Body=body,
        ContentType="application/json",
    )

    return S3RawLocation(bucket=clean_bucket, key=clean_key)


def is_s3_raw_upload_enabled(env: Mapping[str, str] | None = None) -> bool:
    env_values = os.environ if env is None else env
    value = env_values.get(ENABLE_S3_RAW_UPLOAD_ENV, "")
    return value.strip().lower() in {"1", "true", "yes", "on"}


def get_s3_raw_bucket(env: Mapping[str, str] | None = None) -> str:
    env_values = os.environ if env is None else env
    bucket = env_values.get(S3_RAW_BUCKET_ENV, "")
    return _clean_bucket(bucket)


def upload_raw_payload_if_enabled(
    payload: dict,
    source: str,
    symbol: str,
    run_date: date,
    filename: str,
    s3_client: Any | None = None,
    env: Mapping[str, str] | None = None,
) -> S3RawLocation | None:
    if not is_s3_raw_upload_enabled(env):
        return None

    bucket = get_s3_raw_bucket(env)
    key = build_raw_object_key(
        source=source,
        symbol=symbol,
        run_date=run_date,
        filename=filename,
    )

    client = s3_client if s3_client is not None else _build_default_s3_client()
    return upload_json_to_s3(
        s3_client=client,
        bucket=bucket,
        key=key,
        payload=payload,
    )


def _build_default_s3_client() -> Any:
    try:
        import boto3
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "ENABLE_S3_RAW_UPLOAD is enabled, but boto3 is not installed. "
            "Install boto3 or pass an injected s3_client."
        ) from exc

    return boto3.client("s3")


def _clean_bucket(bucket: str) -> str:
    clean_value = bucket.strip()
    if not clean_value:
        raise ValueError("bucket must not be empty")
    if clean_value.startswith("s3://"):
        raise ValueError("bucket must be a bucket name, not an s3:// URI")
    return clean_value


def _clean_s3_key(key: str) -> str:
    clean_value = key.strip().strip("/")
    if not clean_value:
        raise ValueError("key must not be empty")
    if clean_value.startswith("s3://"):
        raise ValueError("key must be an object key, not an s3:// URI")
    return clean_value


def _clean_path_part(value: str, field_name: str) -> str:
    clean_value = value.strip().strip("/")
    if not clean_value:
        raise ValueError(f"{field_name} must not be empty")
    if "/" in clean_value:
        raise ValueError(f"{field_name} must be one path segment")
    return clean_value


def _clean_filename(filename: str) -> str:
    clean_value = filename.strip().strip("/")
    if not clean_value:
        raise ValueError("filename must not be empty")
    if "/" in clean_value:
        raise ValueError("filename must not include directories")
    return clean_value
