from datetime import date
from de_lakehouse_pipeline.ingest.cloud_storage import (
    build_raw_object_key,
    upload_raw_payload_if_enabled,
    CloudStorageConfigError,
    CloudStorageUploadError,
    )

from de_lakehouse_pipeline.ingest import cloud_storage

import pytest

class FakeS3Client:
    def __init__(self):
        self.objects = []

    def put_object(self, **kwargs):
        self.objects.append(kwargs)

class FailingS3Client:
    def put_object(self, **kwargs):
        raise RuntimeError("upload failed")

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


def test_upload_enabled_creates_default_client(monkeypatch):
    fake_client = FakeS3Client()

    monkeypatch.setattr(
        cloud_storage,
        "create_s3_client",
        lambda: fake_client,
    )

    result = cloud_storage.upload_raw_payload_if_enabled(
        payload={"symbol": "AAPL"},
        source="alpha_vantage",
        symbol="AAPL",
        run_date=date(2026, 5, 26),
        filename="stock.json",
        env={
            "ENABLE_S3_RAW_UPLOAD": "true",
            "S3_RAW_BUCKET": "test-bucket",
        },
    )

    assert result is not None
    assert len(fake_client.objects) == 1
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