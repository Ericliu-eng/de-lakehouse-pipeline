# S3 Live Upload and Read-Back — 2026-09-30

A production pipeline run with S3 upload enabled, followed by a read-back of
the uploaded object. It used a personal AWS development account through the
`personal` AWS CLI profile, the development PostgreSQL 16 container, and the
live Alpha Vantage API. No credentials, account IDs, ETags, or version IDs are
recorded here.

## Bucket state

- Bucket `eric-de-lakehouse-raw-dev-20260918` exists in `us-west-2` and is
  managed by `infra/terraform`.
- `terraform plan` for the current module (read-only; not applied): **2 to
  add, 1 to change, 0 to destroy**. It would create the new lifecycle
  configuration, add default tags to the bucket in place, and create the
  `raw_writer` IAM policy, which is not currently present in the account.

## Run

```bash
export AWS_PROFILE=personal AWS_DEFAULT_REGION=us-west-2
export ENABLE_S3_RAW_UPLOAD=true S3_RAW_BUCKET=eric-de-lakehouse-raw-dev-20260918
python -m de_lakehouse_pipeline.cli run_stock --symbol AAPL
```

```text
Saved raw stock data to data/raw/2026-09-30/AAPL/stock.json
Uploaded raw stock data to s3://eric-de-lakehouse-raw-dev-20260918/raw/alpha_vantage/symbol=AAPL/date=2026-09-30/stock.json
Stock pipeline finished successfully for symbol=AAPL with 1 new row(s)
```

Wall time: 6.8 s, including the API call. AAPL `alpha_vantage` rows in
`market_bars` went from 184 to 185; the latest bar is 2026-09-29.

## Read-back

```bash
aws s3api head-object --bucket eric-de-lakehouse-raw-dev-20260918 \
  --key raw/alpha_vantage/symbol=AAPL/date=2026-09-30/stock.json
aws s3api get-object --bucket eric-de-lakehouse-raw-dev-20260918 \
  --key raw/alpha_vantage/symbol=AAPL/date=2026-09-30/stock.json readback.json
```

| Check | Result |
| --- | --- |
| Content type | `application/json` |
| Server-side encryption | `AES256` (bucket default) |
| Size | 17,563 bytes |
| Versioning | Object has a version ID |
| Payload vs. local raw file | Equal after parsing; canonical SHA-256 `488e9097155ac4f7…` for both |
| Bars in payload | 100, latest 2026-09-29 |

The upload stores the payload as sorted, indented JSON, so the bytes differ
from the local file's key order while the parsed payloads are identical.

## Coverage without AWS

The same path is covered in CI by `tests/integration/test_cloud_storage_moto.py`
(including "upload failure leaves the warehouse untouched") and the bucket
configuration by `infra/terraform/tests/raw_bucket.tftest.hcl`.
