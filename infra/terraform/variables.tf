variable "aws_region" {
  description = "AWS region for cloud storage resources."
  type        = string
  default     = "us-west-2"
}

variable "environment" {
  description = "Deployment environment, applied to every resource as a tag."
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be dev, staging, or prod."
  }
}

variable "raw_bucket_name" {
  description = "S3 bucket name for raw payload storage."
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$", var.raw_bucket_name))
    error_message = "raw_bucket_name must be 3-63 lowercase letters, digits, dots, or hyphens."
  }
}

variable "noncurrent_version_retention_days" {
  description = "Days to keep overwritten raw object versions before they expire."
  type        = number
  default     = 90

  validation {
    condition     = var.noncurrent_version_retention_days >= 1
    error_message = "noncurrent_version_retention_days must be at least 1."
  }
}
