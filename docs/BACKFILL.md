# BACKFILL

## Purpose
This document explains how range backfill works in the pipeline.

## Current Scope
The current backfill script accepts a start date and end date, validates the range,
and iterates through each date that would be processed.

## Command
```bash
python scripts/backfill.py --start 2026-01-01 --end 2026-01-07