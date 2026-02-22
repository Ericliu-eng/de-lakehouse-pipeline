# Weekly Log

## Week 01

### Day 1 (2026-02-19)
- Done: repo skeleton (Makefile targets + CI + docs)
- Proof: `docs/proof/`
- Next: implement the first main feature block skeleton

### Day 2 (2026-2-21)
### What I did
- Implemented a minimal ETL pipeline (Extract → Transform → Load)
- Read data from `data/raw/sample.csv`
- Applied simple transformations (drop missing values, filter rows)
- Saved output to `data/processed/output.csv`
- Added proof of execution in `docs/proof/`
- Updated README with run instructions

### What I learned
- How to structure a data engineering repo (src/, data/, docs/)
- How to run Python modules using `python -m`
- Importance of reproducibility (Makefile + README)
- Basic ETL pipeline workflow

### Issues / Challenges
- Module import issue (`de_lakehouse_pipeline` not found)
- Learned to fix it using `python -m src.de_lakehouse_pipeline.main`

### Next steps
- Improve pipeline structure
- Add logging and configuration


### make up Day 03 in(2026-2-21)
### What I did
- Introduced a transform(df) function to isolate core data processing logic.
- Kept main() as the pipeline entry (file I/O + orchestration).

### What I learned
Difference between unit tests (logic) and pipeline execution (orchestration)
Importance of separating core logic (transform) from I/O (main)
How to design:
normal case tests
edge case tests
failure case tests
Testing improves confidence and makes code reproducible
### Issues / Challenges
Initially confused about what to test (main vs transform)
Learned that:
transform → unit test
main → behavior / integration

### Next steps
Push code and ensure CI passes
Continue improving pipeline structure and documentation



### make up Day 03 in(2026-2-21)
### What I did
- How to write a smoke (E2E) test using `tmp_path`
- Difference between unit tests and pipeline-level tests
- How Makefile helps standardize commands (`make test`, `make smoke`, etc.)

### Issues / Challenges
- `make run` failed due to module import issue (`src/` structure not recognized)
- Needed to refactor pipeline to support testing (add `run_pipeline`)

### Next steps
- Fix `make run` so pipeline can run from CLI
- Re-run and update proof with successful output