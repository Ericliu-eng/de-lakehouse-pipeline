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