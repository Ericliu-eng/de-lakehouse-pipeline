# Fresh-Clone Quickstart — 2026-09-25

Followed the README quickstart from a new clone of `main` at commit `1ee070e`
(the v1.1.0 code before release documentation) on Windows 11, Git Bash, GNU
Make, and system Python 3.11.0.

## Commands and results

```bash
git clone https://github.com/Ericliu-eng/de-lakehouse-pipeline.git lhc
cd lhc
make setup          # 3 min 2 s, exit 0
cp .env.example .env
make db-migrate     # exit 0
make db-seed        # exit 0
make lint           # All checks passed!
make test           # exit 0
```

`make test` results:

| Target | Result |
| --- | --- |
| `make unit` | 130 passed |
| `make smoke` | 8 passed, 8 deselected |
| `make smoke-db` | 6 passed, 10 deselected |
| `make integration` | 13 passed |
| **Total** | **157 passed, 0 failed** |

The only warning came from a dependency: Starlette reports that using `httpx`
with its test client is deprecated.

## Environment notes

- PostgreSQL 16 ran in the existing `de_lakehouse_db` container, using a
  throwaway database (`DB_NAME=lakehouse_release`) that was dropped afterwards.
  `make db-up` was not repeated from the clone because the Compose file pins
  the container name, which was already in use.
- No API key was configured; the suite uses sample data and mocks.
- The first attempt, cloned under a deep temporary directory, failed during
  `make setup` with `OSError: [Errno 2] No such file or directory` for a file
  under `site-packages\dagster\_core\storage\alembic\versions`. Dagster's
  nested files exceeded Windows' 260-character path limit. Cloning to a short
  path fixed it; this is now in the troubleshooting section of
  [DEV_SETUP](../DEV_SETUP.md).

## CI

The GitHub Actions run for the same commit on `main` succeeded:
[run 36215319646](https://github.com/Ericliu-eng/de-lakehouse-pipeline/actions/runs/36215319646).
