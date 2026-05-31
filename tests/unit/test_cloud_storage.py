from datetime import date

import pytest

from de_lakehouse_pipeline.ingest.cloud_storage import (
    build_raw_object_key,
    upload_raw_payload_if_enabled,
)


class FakeS3Client:
    def __init__(self) -> None:
        self.put_object_calls = []

    def put_object(self, **kwargs) -> None:
        self.put_object_calls.append(kwargs)


def test_build_raw_object_key_uses_partitioned_layout() -> None:
    key = build_raw_object_key(
        source="alpha_vantage",
        symbol="aapl",
        run_date=date(2026, 5, 25),
        filename="stock.json",
    )

    assert key == "raw/alpha_vantage/symbol=AAPL/date=2026-05-25/stock.json"


def test_upload_raw_payload_if_enabled_skips_when_flag_is_off() -> None:
    client = FakeS3Client()

    uri = upload_raw_payload_if_enabled(
        payload={"symbol": "AAPL"},
        source="alpha_vantage",
        symbol="AAPL",
        run_date=date(2026, 5, 25),
        filename="stock.json",
        s3_client=client,
        env={},
    )

    assert uri is None
    assert client.put_object_calls == []


def test_upload_raw_payload_if_enabled_uploads_when_flag_is_on() -> None:
    client = FakeS3Client()

    uri = upload_raw_payload_if_enabled(
        payload={"symbol": "AAPL"},
        source="alpha_vantage",
        symbol="AAPL",
        run_date=date(2026, 5, 25),
        filename="stock.json",
        s3_client=client,
        env={
            "ENABLE_S3_RAW_UPLOAD": "true",
            "S3_RAW_BUCKET": "de-lakehouse-raw",
        },
    )

    expected_key = "raw/alpha_vantage/symbol=AAPL/date=2026-05-25/stock.json"
    assert uri == f"s3://de-lakehouse-raw/{expected_key}"
    assert client.put_object_calls[0]["Bucket"] == "de-lakehouse-raw"
    assert client.put_object_calls[0]["Key"] == expected_key


def test_upload_raw_payload_if_enabled_requires_bucket_when_flag_is_on() -> None:
    with pytest.raises(ValueError, match="S3_RAW_BUCKET is required"):
        upload_raw_payload_if_enabled(
            payload={"symbol": "AAPL"},
            source="alpha_vantage",
            symbol="AAPL",
            run_date=date(2026, 5, 25),
            filename="stock.json",
            s3_client=FakeS3Client(),
            env={"ENABLE_S3_RAW_UPLOAD": "true"},
        )
