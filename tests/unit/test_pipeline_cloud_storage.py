
from de_lakehouse_pipeline import pipeline


class FakeS3Client:
    def __init__(self):
        self.objects = []
                #接收很多个“带名字的参数”，然后把它们自动打包成一个 dict。
    def put_object(self, **kwargs):
        self.objects.append(kwargs)

def test_run_stock_uploads_when_s3_is_enabled(monkeypatch, tmp_path):
    payload = {
        "Meta Data": {
            "2. Symbol": "AAPL",
            "5. Time Zone": "UTC",
        },
        "Time Series (Daily)": {},
    }
    fake_client = FakeS3Client()

    monkeypatch.setattr(pipeline, "fetch_daily_stock", lambda symbol: payload)
    monkeypatch.setenv("ENABLE_S3_RAW_UPLOAD", "true")
    monkeypatch.setenv("S3_RAW_BUCKET", "test-bucket")

    pipeline.run_stock(
        symbol="AAPL",
        root=tmp_path,
        s3_client=fake_client,
    )

    assert len(fake_client.objects) == 1
    assert fake_client.objects[0]["Bucket"] == "test-bucket"