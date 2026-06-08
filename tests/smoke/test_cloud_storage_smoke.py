from datetime import date

from de_lakehouse_pipeline.ingest.cloud_storage import upload_raw_payload_if_enabled


class FakeS3Client:
    def __init__(self):
        self.objects = []

    def put_object(self, **kwargs):
        self.objects.append(kwargs)


def test_cloud_storage_raw_upload_smoke():
    fake_client = FakeS3Client()

    result = upload_raw_payload_if_enabled(
        payload={"symbol": "AAPL"},
        source="alpha_vantage",
        symbol="AAPL",
        run_date=date(2026, 5, 28),
        filename="stock.json",
        s3_client=fake_client,
        env={
            "ENABLE_S3_RAW_UPLOAD": "true",
            "S3_RAW_BUCKET": "test-bucket",
        },
    )

    assert result is not None
    assert result.uri == (
        "s3://test-bucket/raw/alpha_vantage/"
        "symbol=AAPL/date=2026-05-28/stock.json"
    )
    assert len(fake_client.objects) == 1

    uploaded_object = fake_client.objects[0]

    assert uploaded_object["Bucket"] == "test-bucket"
    assert uploaded_object["Key"] == (
        "raw/alpha_vantage/symbol=AAPL/date=2026-05-28/stock.json"
    )
    assert uploaded_object["ContentType"] == "application/json"

