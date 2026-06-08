
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
"""1. 用 _require_non_empty 检查 source
2. 用 _require_non_empty 检查 symbol，然后把 symbol 变成大写
3. 用 _require_non_empty 检查 filename
4. 用 run_date.isoformat() 变成 2026-05-26
5. 用 f-string 拼接路径
6. return 这个路径"""
#raw/alpha_vantage/symbol=AAPL/date=2026-05-26/stock.json
def build_raw_object_key(source, symbol, run_date, filename):
    clean_source =  _require_non_empty('source',source)
    clean_symbol = _require_non_empty('symbol',symbol).upper()
    clean_filename = _require_non_empty("filename", filename)


    return (
        f"raw/{clean_source}/"
        f"symbol={clean_symbol}/"
        f"date={run_date.isoformat()}/"
        f"{clean_filename}"
    )


"""1. 读取环境变量 env
2. 看 ENABLE_S3_RAW_UPLOAD 是否等于 "true"
3. 如果不是 true，直接 return None
4. 如果是 true，检查 S3_RAW_BUCKET 有没有
5. 用 build_raw_object_key 生成 key
6. 如果 s3_client 是 None，raise CloudStorageConfigError
7. 把 payload 转成 JSON bytes
8. 调用 s3_client.put_object(...)
9. 如果上传失败，raise CloudStorageUploadError
10. 成功后 return S3RawLocation(bucket, key)"""
def upload_raw_payload_if_enabled(
    payload,
    source,
    symbol,
    run_date,
    filename,
    s3_client=None,
    env=None,
):
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
        raise CloudStorageConfigError(
            "s3_client is required when ENABLE_S3_RAW_UPLOAD=true"
        )
    
    try:
        #把payload变成一个稳定、可读、可长期保存的原始 JSON 文件：
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
    
"""print(S3RawLocation.bucket)
print(S3RawLocation.key)
print(S3RawLocation.uri)"""