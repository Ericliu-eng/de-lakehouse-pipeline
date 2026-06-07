## Raw Object Key Pattern

Raw files use this partitioned layout:

```text
raw/{source}/symbol={SYMBOL}/date={YYYY-MM-DD}/{filename}
```

Example:

```text
raw/alpha_vantage/symbol=AAPL/date=2026-05-28/stock.json
```

## Least-Privilege IAM Plan

The pipeline only needs permission to upload raw payloads to the configured raw S3 bucket.

Required permission:

- `s3:PutObject` on `arn:aws:s3:::<bucket-name>/raw/*`

The pipeline does not need:

- `s3:DeleteObject`
- `s3:ListAllMyBuckets`
- write access to other buckets
- administrator permissions

Example policy shape:

```json
{
  "Effect": "Allow",
  "Action": ["s3:PutObject"],
  "Resource": "arn:aws:s3:::<bucket-name>/raw/*"
}
```