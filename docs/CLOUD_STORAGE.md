# Cloud Storage

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
