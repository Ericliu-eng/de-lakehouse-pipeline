# Failure Drills

## Goal

This document records reliability drills for the DE lakehouse pipeline.

## Drill 1: API 429 / 500

Failure:
- API returns 429 rate limit
- API returns 500 server error

Expected behavior:
- retry if the error is retryable
- fail clearly after max retries
- log the error message
- do not write partial corrupted data

## Drill 2: Schema Change

Failure:
- upstream JSON response misses expected fields
- upstream JSON response adds unexpected fields

Expected behavior:
- fail with clear validation error
- keep raw payload for debugging
- do not silently load bad rows

## Drill 3: DB Write Failure

Failure:
- database connection fails
- insert / upsert fails

Expected behavior:
- rollback transaction
- log failed step
- do not update watermark if load fails