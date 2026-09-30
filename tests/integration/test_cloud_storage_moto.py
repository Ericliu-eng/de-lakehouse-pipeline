"""Exercise the real boto3 upload path against Moto's in-memory S3."""
import json
from datetime import date
from pathlib import Path
from uuid import uuid4

import boto3
import pytest
from moto import mock_aws
from psycopg import sql

from de_lakehouse_pipeline import pipeline
from de_lakehouse_pipeline.ingest.cloud_storage import (
    CloudStorageUploadError,
    upload_raw_payload_if_enabled,
)
from de_lakehouse_pipeline.load.db.connection import connect, load_db_config

pytestmark = pytest.mark.integration

BUCKET = "lakehouse-raw-test"
SYMBOL = "S3TEST"
PAYLOAD = {
    "Meta Data": {"2. Symbol": SYMBOL, "5. Time Zone": "US/Eastern"},
    "Time Series (Daily)": {
        "2026-09-18": {"1. open": "1", "2. high": "2", "3. low": "1", "4. close": "2", "5. volume": "10"},
    },
}


@pytest.fixture
def s3(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-west-2")
    monkeypatch.setenv("ENABLE_S3_RAW_UPLOAD", "true")
    monkeypatch.setenv("S3_RAW_BUCKET", BUCKET)
    with mock_aws():
        client = boto3.client("s3")
        client.create_bucket(Bucket=BUCKET, CreateBucketConfiguration={"LocationConstraint": "us-west-2"})
        client.put_bucket_encryption(
            Bucket=BUCKET,
            ServerSideEncryptionConfiguration={
                "Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]
            },
        )
        yield client


def test_default_boto3_client_uploads_encrypted_json(s3):
    location = upload_raw_payload_if_enabled(
        payload=PAYLOAD, source="alpha_vantage", symbol="s3test",
        run_date=date(2026, 9, 18), filename="stock.json",
    )

    assert location.uri == f"s3://{BUCKET}/raw/alpha_vantage/symbol=S3TEST/date=2026-09-18/stock.json"
    obj = s3.get_object(Bucket=BUCKET, Key=location.key)
    assert json.loads(obj["Body"].read()) == PAYLOAD
    assert obj["ContentType"] == "application/json"
    assert obj["ServerSideEncryption"] == "AES256"


def test_rerun_on_the_same_day_keeps_the_previous_version(s3):
    s3.put_bucket_versioning(Bucket=BUCKET, VersioningConfiguration={"Status": "Enabled"})
    kwargs = dict(source="alpha_vantage", symbol=SYMBOL, run_date=date(2026, 9, 18), filename="stock.json")

    upload_raw_payload_if_enabled(payload={"run": 1}, **kwargs)
    location = upload_raw_payload_if_enabled(payload={"run": 2}, **kwargs)

    versions = s3.list_object_versions(Bucket=BUCKET, Prefix=location.key)["Versions"]
    assert len(versions) == 2
    assert json.loads(s3.get_object(Bucket=BUCKET, Key=location.key)["Body"].read()) == {"run": 2}


def test_missing_bucket_raises_upload_error(s3, monkeypatch):
    monkeypatch.setenv("S3_RAW_BUCKET", "bucket-that-does-not-exist")

    with pytest.raises(CloudStorageUploadError, match="bucket-that-does-not-exist"):
        upload_raw_payload_if_enabled(
            payload=PAYLOAD, source="alpha_vantage", symbol=SYMBOL,
            run_date=date(2026, 9, 18), filename="stock.json",
        )


@pytest.fixture
def warehouse(monkeypatch):
    cfg = load_db_config()
    schema = "test_s3_" + uuid4().hex
    with connect(cfg) as conn:
        conn.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))

    def open_connection(_cfg=None):
        conn = connect(cfg)
        conn.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(schema)))
        conn.commit()
        return conn

    try:
        with open_connection() as conn:
            root = Path(__file__).resolve().parents[2]
            for name in ["003_market_bars.sql", "004_load_metadata.sql",
                         "006_pipeline_metadata.sql", "008_add_source_to_market_bars.sql"]:
                conn.execute((root / "migrations" / name).read_text(encoding="utf-8"))
        monkeypatch.setattr(pipeline, "connect", open_connection)
        monkeypatch.setattr(pipeline, "wait_for_db", lambda *args, **kwargs: None)
        monkeypatch.setattr(pipeline, "fetch_daily_stock", lambda symbol: PAYLOAD)
        yield open_connection
    finally:
        with connect(cfg) as conn:
            conn.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


@pytest.mark.db
def test_pipeline_stores_the_same_raw_payload_locally_and_in_s3(s3, warehouse, tmp_path):
    local_file = pipeline.run_stock(SYMBOL, root=tmp_path)

    key = f"raw/alpha_vantage/symbol={SYMBOL}/date={date.today().isoformat()}/stock.json"
    uploaded = json.loads(s3.get_object(Bucket=BUCKET, Key=key)["Body"].read())
    assert uploaded == json.loads(local_file.read_text()) == PAYLOAD
    with warehouse() as conn:
        assert conn.execute("SELECT COUNT(*) FROM market_bars").fetchone()[0] == 1


@pytest.mark.db
def test_upload_failure_stops_before_warehouse_writes(s3, warehouse, tmp_path, monkeypatch):
    monkeypatch.setenv("S3_RAW_BUCKET", "bucket-that-does-not-exist")

    with pytest.raises(CloudStorageUploadError):
        pipeline.run_stock(SYMBOL, root=tmp_path)

    with warehouse() as conn:
        for table in ["market_bars", "pipeline_metadata", "load_metadata"]:
            count = conn.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(sql.Identifier(table))).fetchone()[0]
            assert count == 0
