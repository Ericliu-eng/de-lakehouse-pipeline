from datetime import date
from de_lakehouse_pipeline.ingest.cloud_stroage import (
    build_raw_object_key,
    upload_raw_payload_if_enabled,
    CloudStorageConfigError,
    CloudStorageUploadError,
    )

import pytest

class FakeS3Client:
    def __init__(self):
        self.objects = []
                #接收很多个“带名字的参数”，然后把它们自动打包成一个 dict。
    def put_object(self, **kwargs):
        self.objects.append(kwargs)

class FailingS3Client:
    def put_object(self, **kwargs):
        raise RuntimeError("upload failed")

"""输入 aapl
输出路径里的 symbol 应该是 AAPL"""
def test_build_raw_object_key():
    key = build_raw_object_key(
        source="alpha_vantage",
        symbol="aapl",
        run_date=date(2026, 5, 26),
        filename="stock.json",
    )

    assert key == "raw/alpha_vantage/symbol=AAPL/date=2026-05-26/stock.json"



def test_upload_disabled_returns_none():
    result = upload_raw_payload_if_enabled(
        payload={"symbol": "AAPL"},
        source="alpha_vantage",
        symbol="AAPL",
        run_date=date(2026, 5, 26),
        filename="stock.json",
        env={"ENABLE_S3_RAW_UPLOAD": "false"},
    )

    assert result is None

"""不真的上传到 AWS，只是记录有没有被调用。

这个测试要检查：

1. 返回值不是 None
2. 返回值 uri 是正确的 s3://...
3. fake client 里面确实记录了一次 put_object
4. Bucket / Key / ContentType 是正确的"""

def test_upload_enabled_puts_object():
    fake_client = FakeS3Client()

    result = upload_raw_payload_if_enabled(
    payload={"symbol": "AAPL"},
    source="alpha_vantage",
    symbol="AAPL",
    run_date=date(2026, 5, 26),
    filename="stock.json",
    s3_client=fake_client,
    env={
        "ENABLE_S3_RAW_UPLOAD": "true",
        "S3_RAW_BUCKET": "test-bucket",
    },)

    assert result is not None
    assert result.bucket == "test-bucket"
    assert result.key == "raw/alpha_vantage/symbol=AAPL/date=2026-05-26/stock.json"
    assert result.uri == (
        "s3://test-bucket/raw/alpha_vantage/"
        "symbol=AAPL/date=2026-05-26/stock.json"
    )
    assert len(fake_client.objects) == 1    
    
    uploaded_object = fake_client.objects[0]

    assert uploaded_object["Bucket"] == "test-bucket"
    assert uploaded_object["Key"] == (
        "raw/alpha_vantage/symbol=AAPL/date=2026-05-26/stock.json"
    )
    assert uploaded_object["ContentType"] == "application/json"


def test_upload_failure_raises_upload_error():
    failingS3Client  = FailingS3Client()
    #如果出 这个CloudStorageUploadError 就pass
    with pytest.raises(CloudStorageUploadError):
        upload_raw_payload_if_enabled(
        payload={"symbol": "AAPL"},
        source="alpha_vantage",
        symbol="AAPL",
        run_date=date(2026, 5, 26),
        filename="stock.json",
        s3_client=failingS3Client,
        env={
            "ENABLE_S3_RAW_UPLOAD": "true",
            "S3_RAW_BUCKET": "test-bucket",
        },)

def test_upload_enabled_without_bucket_raises_config_error():
    with pytest.raises(CloudStorageConfigError):
        upload_raw_payload_if_enabled(
            payload={"symbol": "AAPL"},
            source="alpha_vantage",
            symbol="AAPL",
            run_date=date(2026, 5, 26),
            filename="stock.json",
            s3_client=FakeS3Client(),
            env={
                "ENABLE_S3_RAW_UPLOAD": "true",
            },
        )


"""1. 调用 upload_raw_payload_if_enabled
2. env 里面 ENABLE_S3_RAW_UPLOAD = "true"
3. env 里面 S3_RAW_BUCKET = "test-bucket"
4. 但是不要传 s3_client
5. 应该 raise CloudStorageConfigError"""
def test_upload_enabled_without_s3_client_raises_config_error():
    with pytest.raises(CloudStorageConfigError):
        upload_raw_payload_if_enabled(
            payload={"symbol": "AAPL"},
            source="alpha_vantage",
            symbol="AAPL",
            run_date=date(2026, 5, 26),
            filename="stock.json",
            s3_client=None,
            env={
                "ENABLE_S3_RAW_UPLOAD": "true",
            },
        )

#edge test 
def test_upload_flag_is_case_insensitive():
    fake_client = FakeS3Client()

    result =upload_raw_payload_if_enabled(
            payload={"symbol": "AAPL"},
            source="alpha_vantage",
            symbol="AAPL",
            run_date=date(2026, 5, 26),
            filename="stock.json",
            s3_client=fake_client,
            env={
                "ENABLE_S3_RAW_UPLOAD": "TRUE",
                "S3_RAW_BUCKET" :"test-bucket"
            },
        )


    assert result is not None
    assert len(fake_client.objects) == 1