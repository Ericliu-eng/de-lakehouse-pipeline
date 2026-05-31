terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Placeholder for Week 15 cloud deployment.
# Later PRs will add:
# - raw S3 bucket
# - least-privilege IAM policy
# - runtime role/user permissions
# - lifecycle and cost controls