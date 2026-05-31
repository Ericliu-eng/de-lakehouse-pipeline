# Cloud Storage

## Purpose

This document explains how the project can optionally upload raw API payloads to S3.

The cloud storage layer is used for keeping a raw copy of source data before transformation and database loading.

## Current Scope

This version supports:

- building a partitioned S3 object key
- optionally uploading raw JSON payloads to S3
- skipping upload when cloud upload is disabled
- validating required environment variables

This PR does not provision AWS infrastructure yet.

## Environment Variables

| Variable | Required | Description |
|---|---:|---|
| `ENABLE_S3_RAW_UPLOAD` | No | Must be set to `true` to enable S3 upload |
| `S3_RAW_BUCKET` | Yes, if upload is enabled | S3 bucket name for raw payload storage |

## Raw Object Key Pattern

Raw files use this partitioned layout:

```text
raw/{source}/symbol={SYMBOL}/date={YYYY-MM-DD}/{filename}