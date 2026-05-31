# Terraform Scaffold

This directory contains the initial Terraform scaffold for Week 15 cloud deployment work.

## Current Scope

This PR only adds the Terraform structure.

It does not create real AWS resources yet.

## Planned Resources

Later PRs will add:

- S3 raw storage bucket
- least-privilege IAM policy
- runtime permissions for upload
- cost controls and lifecycle rules

## Commands

```bash
terraform fmt
terraform init
terraform plan