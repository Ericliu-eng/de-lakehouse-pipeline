# Offline checks with a mocked AWS provider: no credentials or AWS calls needed.
mock_provider "aws" {
  mock_resource "aws_s3_bucket" {
    defaults = {
      arn = "arn:aws:s3:::lakehouse-raw-test"
    }
  }
}

variables {
  raw_bucket_name = "lakehouse-raw-test"
}

run "raw_bucket_is_private_encrypted_and_versioned" {
  command = apply

  assert {
    condition = alltrue([
      aws_s3_bucket_public_access_block.raw.block_public_acls,
      aws_s3_bucket_public_access_block.raw.block_public_policy,
      aws_s3_bucket_public_access_block.raw.ignore_public_acls,
      aws_s3_bucket_public_access_block.raw.restrict_public_buckets,
    ])
    error_message = "All public access must be blocked."
  }

  assert {
    condition     = one(one(aws_s3_bucket_server_side_encryption_configuration.raw.rule).apply_server_side_encryption_by_default).sse_algorithm == "AES256"
    error_message = "Objects must be encrypted at rest by default."
  }

  assert {
    condition     = one(aws_s3_bucket_versioning.raw.versioning_configuration).status == "Enabled"
    error_message = "Versioning must be enabled."
  }

  assert {
    condition     = one(aws_s3_bucket_ownership_controls.raw.rule).object_ownership == "BucketOwnerEnforced"
    error_message = "ACLs must be disabled."
  }
}

run "overwritten_versions_expire_but_current_objects_are_kept" {
  command = apply

  assert {
    condition     = one(one(aws_s3_bucket_lifecycle_configuration.raw.rule).noncurrent_version_expiration).noncurrent_days == 90
    error_message = "Noncurrent raw versions must expire after the retention window."
  }

  assert {
    condition     = length(one(aws_s3_bucket_lifecycle_configuration.raw.rule).expiration) == 0
    error_message = "Current raw objects must never expire."
  }
}

run "writer_policy_is_put_only_on_the_raw_prefix" {
  command = apply

  assert {
    condition     = jsondecode(aws_iam_policy.raw_writer.policy).Statement[0].Action == ["s3:PutObject"]
    error_message = "The pipeline role may only put objects."
  }

  assert {
    condition     = jsondecode(aws_iam_policy.raw_writer.policy).Statement[0].Resource == "arn:aws:s3:::lakehouse-raw-test/raw/*"
    error_message = "Writes must be limited to the raw/ prefix."
  }
}

run "invalid_environment_is_rejected" {
  command = plan

  variables {
    environment = "production"
  }

  expect_failures = [var.environment]
}
