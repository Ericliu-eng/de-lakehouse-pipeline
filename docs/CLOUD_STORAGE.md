# Cloud Storage v1

## Purpose

Week 15 introduces cloud raw storage for the lakehouse pipeline. The first
cloud target is AWS S3.

The goal of this version is to define a stable raw object layout and
least-privilege IAM contract before wiring the pipeline to real AWS APIs.

## Cloud Target

```text
Provider: AWS
Service: S3
Layer: raw landing
```

Recommended bucket name for the project:

```text
de-lakehouse-raw
```

If this name is already taken in AWS, use a globally unique variant:

```text
de-lakehouse-raw-<your-name-or-account-id>
```

## Raw Object Layout

All raw API responses should use this object key pattern:

```text
raw/<source>/symbol=<symbol>/date=<YYYY-MM-DD>/<filename>
```

For Alpha Vantage daily stock data:

```text
raw/alpha_vantage/symbol=AAPL/date=2026-05-25/stock.json
```

Full S3 URI:

```text
s3://de-lakehouse-raw/raw/alpha_vantage/symbol=AAPL/date=2026-05-25/stock.json
```

This layout keeps the raw lake partitioned by:

- source
- stock symbol
- run date

## Local Contract

The object-key contract is implemented locally in:

```text
src/de_lakehouse_pipeline/ingest/cloud_storage.py
```

Unit tests live in:

```text
tests/unit/test_cloud_storage.py
```

Validation:

```bash
make -f Makefile cloud-storage-test
make -f Makefile unit
```

## Optional Pipeline Upload

S3 upload is disabled by default. Enable it only when you want the local
pipeline to also write a copy of the raw payload to AWS:

```bash
ENABLE_S3_RAW_UPLOAD=true
S3_RAW_BUCKET=de-lakehouse-raw
```

Then run the pipeline normally:

```bash
make -f Makefile run SYMBOL=AAPL
```

The pipeline always writes the local raw JSON file first. If cloud upload is
enabled, it also uploads the same raw payload to the S3 raw partition path.

## Runtime Dependency

Real AWS upload uses `boto3`, which is listed in `requirements.txt`.

Local unit tests do not require AWS credentials because they use an injected
fake S3 client.

## IAM Contract

The pipeline writer should only be allowed to write and inspect objects under
the raw prefix.

Minimum S3 permissions:

```text
s3:PutObject
s3:GetObject
s3:ListBucket
```

Recommended least-privilege scope:

```text
Bucket: arn:aws:s3:::de-lakehouse-raw
Objects: arn:aws:s3:::de-lakehouse-raw/raw/*
```

Example IAM policy shape:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:ListBucket"],
      "Resource": "arn:aws:s3:::de-lakehouse-raw",
      "Condition": {
        "StringLike": {
          "s3:prefix": ["raw/*"]
        }
      }
    },
    {
      "Effect": "Allow",
      "Action": ["s3:PutObject", "s3:GetObject"],
      "Resource": "arn:aws:s3:::de-lakehouse-raw/raw/*"
    }
  ]
}
```

## Current Status

Implemented:

- AWS chosen as cloud target
- raw object key standard
- S3 URI builder
- mock-testable JSON upload interface
- optional pipeline upload switch through `ENABLE_S3_RAW_UPLOAD`
- unit tests for partitioned S3 paths
- least-privilege IAM design

Not implemented yet:

- bucket creation automation
- cloud credentials configuration
- manual validation against a real AWS account

## Next Step

Install `boto3`, configure AWS credentials, and validate one manual upload
against a real S3 bucket:

```text
boto3.client("s3")
```

The upload interface already accepts an injected client, so production code can
pass a real `boto3` client while unit tests keep using a fake client.
