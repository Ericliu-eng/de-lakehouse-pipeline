# Secrets and Cost

## Secrets

| Secret | Used by | Where it lives | How it is sent |
| --- | --- | --- | --- |
| `ALPHA_VANTAGE_API_KEY` | Daily ingestion, date backfill | `.env` (git-ignored) | Query parameter (required by the API) |
| `TIINGO_API_TOKEN` | History backfill | `.env` (git-ignored) | `Authorization` header |
| AWS credentials | Optional S3 upload, Terraform | AWS profile or role, never `.env` | boto3 / Terraform credential chain |
| Database password | All database access | `.env`; local development default only | psycopg connection |

Rules:

- `.env` and `infra/terraform/terraform.tfstate*` are git-ignored; only
  `.env.example`, with empty values, is committed.
- **The retry helper masks credentials in HTTP and connection errors.** The Alpha Vantage key must travel in
  the URL, and `requests` includes the full URL in `HTTPError` and
  `ConnectionError` messages, which the pipeline logs on failure. The retry
  helper replaces `apikey` and `token` values with `***` before re-raising and
  drops the original exception from the chain.
- Tiingo's token is sent in a header, so it never appears in a URL.
- Proof files record commands and results, never credentials, AWS account IDs,
  or ETags.
- An Alpha Vantage key that appeared in early commit history was rotated on
  2026-10-04. History was not rewritten: GitHub keeps pull-request refs to the
  old commits, so rotation, not a rewrite, is what retires a leaked key.

`urllib3` logs request URLs at `DEBUG`. The pipeline logs at `INFO`; do not
enable `DEBUG` logging for `urllib3` with a real key configured.

## Cost

The only billable cloud resource is the optional S3 bucket. Sizes are measured
from the saved payloads; prices are S3 Standard list prices in `us-west-2` at
the time of writing (storage about $0.023 per GB-month, PUT requests about
$0.005 per 1,000). Check current AWS pricing before relying on them.

| Item | Volume | Approximate monthly cost |
| --- | --- | --- |
| Daily Alpha Vantage payloads | 10 symbols × 17.8 KB median × ~30 runs ≈ 5.3 MB added per month | < $0.001 |
| One-off Tiingo history | 10 files, 34.4 MB total | < $0.001 |
| PUT requests | ~300 per month (daily runs) | ≈ $0.0015 |
| Noncurrent versions | Only from same-day reruns; expire after 90 days | negligible |

A year of daily runs stays well under 1 GB, or a few cents per month. The
lifecycle rule bounds the growth of overwritten versions. PostgreSQL, Dagster,
and the API run locally, so they add no cloud cost.

To stop all charges, empty the bucket (including object versions) and run
`terraform destroy` in `infra/terraform`.
