# Cost Notes

This document summarizes expected cloud costs and cost-control decisions for the Week 16 AWS Terraform setup.

## Current Cloud Scope

The current Terraform stack creates:

- One S3 bucket for raw pipeline payloads
- One IAM policy for raw payload uploads

No always-on compute resources are created.

## Expected Cost Profile

The current setup should be low cost because:

- S3 charges mainly for stored data, requests, and data transfer.
- Raw payload files are small JSON API responses.
- The pipeline uploads only when `ENABLE_S3_RAW_UPLOAD=true`.
- No EC2, ECS, RDS, Airflow, or managed orchestration service is currently provisioned.

## Main Cost Drivers

Potential cost drivers:

- Number of raw files uploaded
- Size of raw API payloads
- S3 PUT request volume
- Long-term retention of raw data
- Cross-region or internet data transfer, if added later

## Cost Controls

Current controls:

- Uploads are disabled by default.
- Uploads require explicit `ENABLE_S3_RAW_UPLOAD=true`.
- The IAM policy allows only `s3:PutObject` on the `raw/*` prefix.
- Terraform resources can be destroyed cleanly after testing.

Recommended controls for future work:

- Add an S3 lifecycle policy for old raw files.
- Keep dev/test buckets separate from production buckets.
- Avoid storing large derived datasets in the raw bucket.
- Use Terraform `plan` before every `apply`.
- Run `terraform destroy` after short-lived demos or experiments.

## Cleanup Command

From the Terraform directory:
```bash
terraform destroy -var="raw_bucket_name=<your-raw-bucket-name>"
```