
import json
import os

ENABLE_S3_RAW_UPLOAD_ENV = "ENABLE_S3_RAW_UPLOAD"
S3_RAW_BUCKET_ENV = "S3_RAW_BUCKET"

class S3RawLocation:
    def __init__(self, bucket: str, key: str):
        self.bucket = bucket
        self.key = key

    @property
    def uri(self) -> str:
        return f"s3://{self.bucket}/{self.key}"

class CloudStorageConfigError(ValueError):
    """Raised when cloud storage configuration is invalid."""

class CloudStorageUploadError(RuntimeError):
    """Raised when raw payload upload fails."""

def _require_non_empty(name, value):
    if value is None:
        raise CloudStorageConfigError(f"{name} must be provided")

    clean_value = str(value).strip()

    if not clean_value:
        raise CloudStorageConfigError(f"{name} must be provided")

    return clean_value

def build_raw_object_key(source, symbol, run_date, filename):
    """Return the partitioned key, e.g. raw/alpha_vantage/symbol=AAPL/date=2026-05-26/stock.json."""
    clean_source =  _require_non_empty('source',source)
    clean_symbol = _require_non_empty('symbol',symbol).upper()
    clean_filename = _require_non_empty("filename", filename)


    return (
        f"raw/{clean_source}/"
        f"symbol={clean_symbol}/"
        f"date={run_date.isoformat()}/"
        f"{clean_filename}"
    )


def upload_raw_payload_if_enabled(
    payload,
    source,
    symbol,
    run_date,
    filename,
    s3_client=None,
    env=None,
):
    """Upload a raw payload to S3 when ENABLE_S3_RAW_UPLOAD is true; otherwise return None."""
    env_values = os.environ if env is None else env

    upload_enabled = env_values.get(ENABLE_S3_RAW_UPLOAD_ENV, "").lower() == "true"
    
    if not upload_enabled:
        return None
    
    bucket = _require_non_empty(
        S3_RAW_BUCKET_ENV,
        env_values.get(S3_RAW_BUCKET_ENV),
    )

    key = build_raw_object_key(
        source=source,
        symbol=symbol,
        run_date=run_date,
        filename=filename,
    )
    if s3_client is None:
        s3_client = create_s3_client()
    try:
        # Sorted keys keep the archived payload byte-stable across reruns.
        body = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")

        s3_client.put_object(
            Bucket=bucket,
            Key=key,
            Body=body,
            ContentType="application/json",
        )

    except Exception as exc:
        raise CloudStorageUploadError(
            f"Failed to upload raw payload to s3://{bucket}/{key}"
        ) from exc

    return S3RawLocation(bucket=bucket, key=key)


def create_s3_client():
    import boto3

    return boto3.client("s3")