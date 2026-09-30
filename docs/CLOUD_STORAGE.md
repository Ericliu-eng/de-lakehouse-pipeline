# Cloud Storage

Raw API payloads can be copied to Amazon S3 in addition to the local
`data/raw/` landing zone. The upload is optional and off by default.

## Runtime Behavior

When `ENABLE_S3_RAW_UPLOAD=true`, all three ingestion paths upload the
unchanged payload right after saving it locally:

| Path | Source | Object filename |
| --- | --- | --- |
| `make run` / `make orchestrate` | `alpha_vantage` | `stock.json` |
| `make backfill` | `alpha_vantage` | `stock.json` |
| `make tiingo-backfill` | `tiingo` | `tiingo.json` |

If no client is supplied, the adapter creates a boto3 client from the standard
AWS credential chain (environment, shared profile, or instance/workload role).
Objects are written as `application/json`.

An upload error raises `CloudStorageUploadError` and fails the run **before any
warehouse write**; the local raw file has already been saved. A disabled flag
skips S3 entirely.

## Raw Object Layout

```text
raw/{source}/symbol={SYMBOL}/date={YYYY-MM-DD}/{filename}
```

Example: `raw/alpha_vantage/symbol=AAPL/date=2026-09-18/stock.json`

Rerunning on the same day writes the same key. Bucket versioning keeps the
previous object as a noncurrent version, which expires after the retention
window (90 days by default).

## Configuration

| Setting | Required | Meaning |
| --- | --- | --- |
| `ENABLE_S3_RAW_UPLOAD` | no | Upload only when `true` (case-insensitive) |
| `S3_RAW_BUCKET` | when enabled | Existing destination bucket |
| AWS credentials | when enabled | An identity allowed `s3:PutObject` on `raw/*` |

Use an AWS profile or role. Never put AWS keys in `.env`, source control,
proof logs, or screenshots. See [Secrets and Cost](SECRETS_AND_COST.md).

## Infrastructure

[`infra/terraform`](../infra/terraform) defines the bucket and the pipeline's
write policy:

- all public access blocked, ACLs disabled (`BucketOwnerEnforced`);
- AES-256 encryption at rest by default;
- versioning, with a lifecycle rule that expires noncurrent versions under
  `raw/` and aborts incomplete multipart uploads after 7 days. Current objects
  are kept: raw data is the source of truth for replays;
- a policy that allows only `s3:PutObject` on `raw/*` — no read, list, or
  delete;
- `Project`, `Environment`, and `ManagedBy` tags on every resource.

Attaching the policy to the pipeline's identity is a deployment step.

## Tests

| Test | What it covers | Needs AWS |
| --- | --- | --- |
| `tests/unit/test_cloud_storage.py` | Key layout, flag handling, config and upload errors (fake client) | No |
| `tests/integration/test_cloud_storage_moto.py` | Real boto3 client against Moto: object body, content type, encryption, versioning on rerun, missing bucket; the pipeline stores the same payload locally and in S3, and an upload failure leaves the warehouse untouched | No |
| `infra/terraform/tests/raw_bucket.tftest.hcl` | `terraform test` with a mocked provider: public access block, encryption, versioning, lifecycle, least-privilege policy, variable validation | No |

All three run in CI.
