variable "aws_region" {
  description = "AWS region for cloud storage resources."
  type        = string
  default     = "us-west-2"
}

variable "raw_bucket_name" {
  description = "S3 bucket name for raw payload storage."
  type        = string
}