# Cloud Storage

## Current Runtime Status

The object-key builder, upload adapter, unit/smoke tests, Terraform bucket, and
least-privilege policy scaffold exist. The main stock pipeline does **not** yet
construct and inject an S3 client. As a result, setting
`ENABLE_S3_RAW_UPLOAD=true` on `run_stock()` or `run_stock_for_date()` raises
`CloudStorageConfigError` before upload. Keep the flag disabled until runtime
client wiring is implemented and tested through the main pipeline.

The adapter itself can be exercised safely with an explicitly supplied client;
the tests use a fake client and do not contact AWS.

## Raw Object Layout

Raw payloads use a source, symbol, and date partition:

```text
raw/{source}/symbol={SYMBOL}/date={YYYY-MM-DD}/{filename}
```

Example: `raw/alpha_vantage/symbol=AAPL/date=2026-05-28/stock.json`

## Least-Privilege IAM

The pipeline requires only `s3:PutObject` for the raw prefix:

```json
{
  "Effect": "Allow",
  "Action": "s3:PutObject",
  "Resource": "arn:aws:s3:::<bucket-name>/raw/*"
}
```

It does not require delete, bucket-listing, cross-bucket write, or administrator
permissions.

## Required Runtime Configuration

| Setting | Required | Meaning |
| --- | --- | --- |
| `ENABLE_S3_RAW_UPLOAD` | no | Upload occurs only when the value is `true` (case-insensitive) |
| `S3_RAW_BUCKET` | when enabled | Destination bucket name |
| AWS credentials/role | when enabled | Must authorize `s3:PutObject` on the raw prefix |

Do not place credentials in `.env`, source control, proof logs, or screenshots.
Prefer a short-lived workload identity or the standard AWS credential chain.
