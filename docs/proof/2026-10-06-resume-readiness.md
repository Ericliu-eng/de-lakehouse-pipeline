# Resume-readiness fixes — local validation

Date: 2026-10-06 (America/Los_Angeles). Branch:
`fix/resume-readiness-fixes`, based on `b008ffa`. Results describe the modified
working tree, not a tagged release or a new GitHub CI run.

## Environment and isolation

- Windows 11, Python 3.13.12, PostgreSQL 16.12, Ruff 0.15.8.
- A dedicated, disposable `postgres:16` container named
  `codex-resume-readiness-postgres`, bound to `127.0.0.1:55439`, with database
  `lakehouse_test`. No existing development database or persistent volume was
  used. Migrations and seed data were applied before testing.
- Test commands override `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, and
  `DB_PASSWORD` for this container; `ENABLE_S3_RAW_UPLOAD=false`.
- The complete benchmark created and dropped its own uniquely named database
  inside that container. It used saved payloads, temporary raw files and
  checkpoints, with S3 and PipeGuard disabled.
- No live Alpha Vantage, Tiingo, AWS, or PipeGuard requests were made for this
  verification. The disposable container was stopped after validation.

## Commands and results

With the isolated database configuration above:

```powershell
.\.venv\Scripts\python.exe -m scripts.migrate
.\.venv\Scripts\python.exe -m scripts.seed_db
.\.venv\Scripts\python.exe -m pytest tests -q --basetemp=tmp/resume-fixes-full-2 --cov --cov-report=term-missing
.\.venv\Scripts\python.exe -m ruff check .
git diff --check
.\.venv\Scripts\python.exe -m scripts.benchmark --repeats 3 --scale-repeats 3 --output docs/proof/2026-10-06-benchmark.md
```

| Check | Result |
| --- | --- |
| Full suite | **281 passed in 17.88 s** |
| Source and orchestration coverage | **88%**, 1,181 covered / 1,347 statements |
| Ruff | All checks passed |
| Diff whitespace | Passed |
| Complete offline benchmark | All seven scenarios completed; [generated report](2026-10-06-benchmark.md) |
| Existing database protection, real PostgreSQL | `--db-name postgres` exited 1 with `Refusing to replace existing database 'postgres'.`; existing DB remained available |
| Benchmark database cleanup | No databases matching `lakehouse_benchmark_%` remained |

The benchmark includes 98,302 warehouse rows, 97,302 history rows inserted in
6.2 s, zero inserts on rerun, 70/70 quality checks, and 30/30 successful daily
runs over the full warehouse. These are local saved-data measurements.
The subsequent database-name length guard does not alter those workloads; its
empty/overlength cases are included in the final full suite.

## Regressions covered

- Both source staging paths reject future dates, non-finite or negative prices,
  inconsistent OHLC, and fractional/negative/overflow volume before any DB
  configuration or write. Valid historical rows and integral decimal strings
  remain supported.
- The manual CLI gate rejects invalid existing PostgreSQL rows before building
  any mart, preserving previous outputs; historical valid data still builds.
- Freshness rejects future dates and uses New York dates even with a UTC-12
  database session.
- Benchmark replay calls the real pipeline with its symbol argument and
  preserves explicit raw partitions. Tests cover reporting/S3 isolation,
  existing/configured DB refusal, concurrent creation failure, owned cleanup,
  environment restoration, and identifier-length protection.
- Python 3.11-only UTC imports were removed from tests. Missing smoke markers
  were restored. CI now selects all tests on Python 3.10 and 3.13.

## Verification limits

Python 3.10 was not installed locally, and the changed CI matrix has not yet
run. Previous release/CI proofs retain their original dates. No new release,
commit, or push is part of this validation.

Concurrent watermark/raw-file writes, forced historical correction, and
automatic mart deletion synchronization remain follow-up work. This project
is verified as a serial local pipeline, not a deployed production service.
