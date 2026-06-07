# Terraform Scaffold

This directory contains the initial Terraform scaffold for Week 15 cloud deployment work.

## Current Scope
This Terraform module creates:
- one raw S3 bucket
- one IAM policy for raw uploads

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