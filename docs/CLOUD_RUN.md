# Cloud Runbook
This document explains how to run the lakehouse pipeline with optional AWS S3 raw payload upload enabled.
## Scope
The current cloud integration supports uploading raw API payloads to an S3 bucket before the data is transformed and loaded into Postgres.

Current cloud resources:

- S3 raw storage bucket
- IAM policy allowing raw payload upload
- Terraform outputs for bucket and policy references

## Required Environment Variables

```bash
ENABLE_S3_RAW_UPLOAD=true
S3_RAW_BUCKET=<your-raw-bucket-name>
AWS_REGION=us-west-2
```