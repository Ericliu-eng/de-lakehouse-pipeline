# Benchmarks and Validation

All numbers below are single-machine local measurements, not production SLAs.
Retry results use scripted HTTP responses rather than live throttling.

## Replayed benchmark

From [the September 25, 2026 benchmark](proof/2026-09-25-benchmark.md)
(`make benchmark`): saved Alpha Vantage payloads and Tiingo history for 10
symbols were replayed into a dedicated PostgreSQL 16 database on a local
Windows machine. No API calls were made, and the development database is never
written to.

### Full price history

| Metric | Result |
| --- | --- |
| Warehouse | 98,276 daily bars · 10 symbols · 1970-01-02 to 2026-09-25 |
| History backfill | 97,276 rows inserted in 7.2 s (about 13,500 rows/s); rerun inserts 0 |
| Cross-source reconciliation | 1,000 days covered by both sources: 0 closes differ by more than 0.5% (max 0.0%) |
| Quality checks over the full warehouse | 60/60 passed in 0.4 s |
| Mart rebuild over the full warehouse | 1.0 s |
| Daily 10-symbol orchestrated run | 15.3 s median; 91% is rebuilding the marts once per symbol |

### Correctness and recovery (1,000-row Alpha Vantage replay)

| Metric | Result |
| --- | --- |
| Rerun of identical payloads | 0 new rows, 0 duplicate keys, watermarks unchanged |
| Incremental run | 50 of 1,000 staged rows loaded (5 new days × 10 symbols) |
| Rejected audit write | No partial writes across `market_bars`, `pipeline_metadata`, `load_metadata` |
| Backfill crash after 4 of 9 trading days | Resume loads the other 5; 0 gaps, 0 duplicates, 1 API fetch per run |
| Quality gate | 2 of 2 injected bad rows caught; marts not rebuilt |
| API retry | 429 → 503 → 200 succeeds on attempt 3; persistent 429 stops after 4 attempts (1 s, 2 s, 4 s backoff) |

## Live runs

| Run | Result |
| --- | --- |
| [Live Tiingo backfill](proof/2026-09-25-tiingo-backfill.md) | 10 API requests, 20 s end to end; development warehouse grew from 1,225 to 98,282 rows; 1,219 overlapping days, 0 beyond 0.5% |
| [Live S3 upload and read-back](proof/2026-09-30-s3-live-upload.md) | Uploaded payload identical to the local raw file |
| [Terraform apply and destroy](proof/W16/2026-06-06-run.txt) | Bucket and IAM policy created and removed |
| [Dagster UI run](proof/W17/screenshots/06-14/image1.png) | `stock_lakehouse_job` succeeded |

## Tests and coverage

On October 4, 2026, `make coverage` against a freshly migrated and seeded
database ran 220 tests and measured **88% line coverage** (1,133 of 1,293
statements). Core modules are covered at 86–100%: pipeline 96%, staging 100%,
quality checks 95%, API client 93%, backfill 86%, Tiingo backfill 98%, CLI 95%,
the CLI orchestrator 92%, and the Dagster job and schedule 100%. The remaining
gaps are the CSV export and the `checkdb` inspection helper (0%), the serving
API (70%), and the standalone entry points of the mart modules.

Coverage includes retry exhaustion, malformed source records, incremental
reruns, checkpoint recovery, quality-gate failures, and a real PostgreSQL
rollback after a rejected audit write. Cloud behavior is tested without AWS
credentials: Moto tests run the real boto3 upload path, and `terraform test`
checks the bucket and policy against a mocked provider.

A fresh clone of [v1.1.0](../CHANGELOG.md) passed `make setup`, migrations,
seeding, `make lint`, and `make test` against PostgreSQL 16
([clean-clone record](proof/2026-09-25-clean-clone.md)).

CI runs on pull requests and pushes to `main`. It provisions PostgreSQL 16,
installs dependencies, migrates and seeds the database, runs Ruff and
`make test`, and validates Terraform.

| Command | Purpose |
| --- | --- |
| `make lint` | Ruff static analysis |
| `make unit` | Unit tests without PostgreSQL |
| `make smoke` | Smoke tests without PostgreSQL |
| `make smoke-db` | Database-backed smoke tests |
| `make integration` | Marts, metadata, and transactional rollback tests |
| `make test` | Default unit, smoke, and integration validation |
| `make test-all` | Collect and run every test under `tests/` |
| `make coverage` | Every test with a line coverage report for `src/` and `orchestration/` |
| `make terraform-validate` | Terraform formatting, initialization, validation, and offline `terraform test` |
| `make benchmark` | Replay saved payloads in a throwaway database and write a results report |

Database-backed tests delete from the tables they use. Run them against a
disposable database (set `DB_NAME`), never against a warehouse you want to keep.
