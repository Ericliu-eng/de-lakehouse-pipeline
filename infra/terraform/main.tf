terraform {
  required_version = ">= 1.5.0"
  # 项目需要使用 AWS provider。 需要 AWS provider 来和 AWS 通信。
  required_providers {
    aws = {
      # 使用 HashiCorp 官方维护的 AWS provider。
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}
#配置 AWS provider。要在哪个 AWS region 创建资源。
provider "aws" {
  region = var.aws_region
}

resource "aws_s3_bucket" "raw" {
  bucket = var.raw_bucket_name
}
#IAM policy 的作用是：定义某个用户、角色、程序可以做什么，不可以做什么。
resource "aws_iam_policy" "raw_writer" {
  name        = "${var.raw_bucket_name}-raw-writer"
  description = "Allow the pipeline to upload raw payloads only."
  #AWS IAM Policy 本质上是 JSON。但是在 Terraform 里写 JSON 很麻烦，所以 Terraform 提供了：
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject"
        ]
        Resource = "${aws_s3_bucket.raw.arn}/raw/*"
      }
    ]
  })
}
