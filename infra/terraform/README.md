# Raw Storage Infrastructure

Terraform for the S3 bucket that stores raw API payloads, and the IAM policy
the pipeline uses to write to it. See [Cloud Storage](../../docs/CLOUD_STORAGE.md)
for runtime behavior.

## Resources

| Resource | Purpose |
| --- | --- |
| `aws_s3_bucket.raw` | Raw payload bucket |
| `aws_s3_bucket_public_access_block.raw` | Blocks all public access |
| `aws_s3_bucket_ownership_controls.raw` | Disables ACLs (`BucketOwnerEnforced`) |
| `aws_s3_bucket_server_side_encryption_configuration.raw` | AES-256 encryption at rest |
| `aws_s3_bucket_versioning.raw` | Keeps overwritten objects as noncurrent versions |
| `aws_s3_bucket_lifecycle_configuration.raw` | Expires noncurrent `raw/` versions; aborts stale multipart uploads |
| `aws_iam_policy.raw_writer` | `s3:PutObject` on `raw/*` only |

The provider tags every resource with `Project`, `Environment`, and
`ManagedBy`.

## Variables

| Variable | Default | Notes |
| --- | --- | --- |
| `raw_bucket_name` | — | Required; globally unique, validated against S3 naming rules |
| `environment` | `dev` | One of `dev`, `staging`, `prod` |
| `aws_region` | `us-west-2` | |
| `noncurrent_version_retention_days` | `90` | Days before overwritten versions expire |

## Validate and Test Offline

No AWS credentials are needed. `terraform test` uses a mocked AWS provider
(Terraform 1.7+).

```bash
make terraform-validate
```

This runs `terraform fmt -check`, `init -backend=false`, `validate`, and
`test`, as CI does.

## Apply

Requires an AWS identity allowed to manage S3 buckets and IAM policies:

```bash
cd infra/terraform
terraform init
terraform plan -var="raw_bucket_name=<unique-name>"
terraform apply -var="raw_bucket_name=<unique-name>"
```

State is stored locally in `terraform.tfstate`, which is git-ignored. Destroy
the stack with `terraform destroy` using the same variables; versioned buckets
must be emptied of all object versions first.
