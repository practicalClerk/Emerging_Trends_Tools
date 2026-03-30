# S3 Bucket for ML Models
resource "aws_s3_bucket" "models" {
  bucket_prefix = "${local.name_prefix}-models-"

  tags = merge(local.common_tags, {
    Purpose = "ml-model-storage"
  })
}

# S3 Bucket Versioning
resource "aws_s3_bucket_versioning" "models" {
  bucket = aws_s3_bucket.models.id

  versioning_configuration {
    status = "Enabled"
  }
}

# S3 Bucket Server-Side Encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "models" {
  bucket = aws_s3_bucket.models.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# S3 Bucket Public Access Block
resource "aws_s3_bucket_public_access_block" "models" {
  bucket = aws_s3_bucket.models.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# S3 Bucket Lifecycle Configuration
resource "aws_s3_bucket_lifecycle_configuration" "models" {
  bucket = aws_s3_bucket.models.id

  rule {
    id     = "delete-old-versions"
    status = "Enabled"

    noncurrent_version_expiration {
      noncurrent_days = 90
    }

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}

# S3 Bucket Policy for ECS/Lambda Access
resource "aws_s3_bucket_policy" "models" {
  bucket = aws_s3_bucket.models.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "ECSAccess"
        Effect    = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
        Action    = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.models.arn,
          "${aws_s3_bucket.models.arn}/*"
        ]
        Condition = {
          StringEquals = {
            "aws:SourceArn" = aws_ecs_task_definition.app.arn
          }
        }
      },
      {
        Sid       = "LambdaAccess"
        Effect    = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.models.arn}/*"
      }
    ]
  })
}

# S3 Objects for Model Files (placeholder - upload actual models)
# These would be created with terraform apply or via separate upload process

# Output S3 bucket info
output "s3_models_bucket" {
  description = "S3 bucket for model storage"
  value       = aws_s3_bucket.models.id
}

output "s3_models_bucket_arn" {
  description = "S3 bucket ARN for model storage"
  value       = aws_s3_bucket.models.arn
}

output "s3_models_bucket_name" {
  description = "S3 bucket name for model storage"
  value       = aws_s3_bucket.models.id
}
