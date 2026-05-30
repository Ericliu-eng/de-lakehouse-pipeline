from datetime import date

import pytest

from de_lakehouse_pipeline.ingest.cloud_storage import (
    build_raw_object_key,
    build_s3_raw_location,
    get_s3_raw_bucket,
    is_s3_raw_upload_enabled,
    upload_raw_payload_if_enabled,
    upload_json_to_s3,
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


def test_build_s3_raw_location_returns_bucket_key_and_uri() -> None:
    location = build_s3_raw_location(
        bucket="de-lakehouse-raw",
        source="alpha_vantage",
        symbol="MSFT",
        run_date=date(2026, 5, 25),
        filename="stock.json",
    )

    assert location.bucket == "de-lakehouse-raw"
    assert location.key == "raw/alpha_vantage/symbol=MSFT/date=2026-05-25/stock.json"
    assert (
        location.uri
        == "s3://de-lakehouse-raw/raw/alpha_vantage/symbol=MSFT/date=2026-05-25/stock.json"
    )


def test_build_s3_raw_location_rejects_uri_as_bucket_name() -> None:
    with pytest.raises(ValueError, match="bucket name"):
        build_s3_raw_location(
            bucket="s3://de-lakehouse-raw",
            source="alpha_vantage",
            symbol="AAPL",
            run_date=date(2026, 5, 25),
            filename="stock.json",
        )


def test_build_raw_object_key_rejects_nested_filename() -> None:
    with pytest.raises(ValueError, match="directories"):
        build_raw_object_key(
            source="alpha_vantage",
            symbol="AAPL",
            run_date=date(2026, 5, 25),
            filename="nested/stock.json",
        )


def test_upload_json_to_s3_writes_json_payload_and_returns_location() -> None:
    client = FakeS3Client()
    key = "raw/alpha_vantage/symbol=AAPL/date=2026-05-25/stock.json"

    location = upload_json_to_s3(
        s3_client=client,
        bucket="de-lakehouse-raw",
        key=key,
        payload={"symbol": "AAPL", "close": 100.25},
    )

    assert location.bucket == "de-lakehouse-raw"
    assert location.key == key
    assert location.uri == f"s3://de-lakehouse-raw/{key}"
    assert client.put_object_calls == [
        {
            "Bucket": "de-lakehouse-raw",
            "Key": key,
            "Body": b'{\n  "close": 100.25,\n  "symbol": "AAPL"\n}',
            "ContentType": "application/json",
        }
    ]


def test_upload_json_to_s3_rejects_uri_as_key() -> None:
    client = FakeS3Client()

    with pytest.raises(ValueError, match="object key"):
        upload_json_to_s3(
            s3_client=client,
            bucket="de-lakehouse-raw",
            key="s3://de-lakehouse-raw/raw/file.json",
            payload={"ok": True},
        )

    assert client.put_object_calls == []


def test_s3_raw_upload_flag_defaults_to_disabled() -> None:
    assert is_s3_raw_upload_enabled({}) is False


def test_s3_raw_upload_flag_accepts_true_values() -> None:
    assert is_s3_raw_upload_enabled({"ENABLE_S3_RAW_UPLOAD": "true"}) is True
    assert is_s3_raw_upload_enabled({"ENABLE_S3_RAW_UPLOAD": "1"}) is True
    assert is_s3_raw_upload_enabled({"ENABLE_S3_RAW_UPLOAD": "yes"}) is True


def test_get_s3_raw_bucket_reads_environment_contract() -> None:
    assert get_s3_raw_bucket({"S3_RAW_BUCKET": "de-lakehouse-raw"}) == "de-lakehouse-raw"


def test_upload_raw_payload_if_enabled_skips_when_flag_is_off() -> None:
    client = FakeS3Client()

    location = upload_raw_payload_if_enabled(
        payload={"symbol": "AAPL"},
        source="alpha_vantage",
        symbol="AAPL",
        run_date=date(2026, 5, 25),
        filename="stock.json",
        s3_client=client,
        env={},
    )

    assert location is None
    assert client.put_object_calls == []


def test_upload_raw_payload_if_enabled_uploads_when_flag_is_on() -> None:
    client = FakeS3Client()

    location = upload_raw_payload_if_enabled(
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

    assert location is not None
    assert location.uri == (
        "s3://de-lakehouse-raw/"
        "raw/alpha_vantage/symbol=AAPL/date=2026-05-25/stock.json"
    )
    assert client.put_object_calls[0]["Bucket"] == "de-lakehouse-raw"
    assert (
        client.put_object_calls[0]["Key"]
        == "raw/alpha_vantage/symbol=AAPL/date=2026-05-25/stock.json"
    )


def test_upload_raw_payload_if_enabled_requires_bucket_when_flag_is_on() -> None:
    client = FakeS3Client()

    with pytest.raises(ValueError, match="bucket must not be empty"):
        upload_raw_payload_if_enabled(
            payload={"symbol": "AAPL"},
            source="alpha_vantage",
            symbol="AAPL",
            run_date=date(2026, 5, 25),
            filename="stock.json",
            s3_client=client,
            env={"ENABLE_S3_RAW_UPLOAD": "true"},
        )

    assert client.put_object_calls == []
