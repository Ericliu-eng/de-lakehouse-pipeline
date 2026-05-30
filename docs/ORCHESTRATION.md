## Current Orchestration Status

The current orchestration layer is implemented as a local skeleton in `orchestration/dagster_pipeline.py`.

It defines the expected pipeline execution order:

1. ingest raw stock data
2. load raw data to database
3. run transformations
4. run quality checks
5. build marts

At this stage, these steps are placeholders. They do not yet call the production pipeline functions.

The purpose of this version is to establish the orchestration structure, step naming, timestamp tracking, and run summary format before connecting real pipeline functions.