output "raw_bucket_name" {
  description = "Configured raw S3 bucket name."
  value       = var.raw_bucket_name
}
output "raw_bucket_arn" {
  description = "ARN of the raw S3 bucket."
  value       = aws_s3_bucket.raw.arn
}

output "raw_writer_policy_arn" {
  description = "ARN of the IAM policy that allows raw payload uploads."
  value       = aws_iam_policy.raw_writer.arn
}
