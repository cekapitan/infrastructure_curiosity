resource "aws_s3_bucket" "archive" {
  region = var.region

  bucket        = var.bucket_name
  force_destroy = false
  tags          = var.tags
}

resource "aws_s3_bucket_public_access_block" "archive" {
  region = var.region

  bucket                  = aws_s3_bucket.archive.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "archive" {
  region = var.region

  bucket = aws_s3_bucket.archive.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "archive" {
  region = var.region

  bucket                                 = aws_s3_bucket.archive.id
  transition_default_minimum_object_size = "all_storage_classes_128K"

  rule {
    id     = "same-day-standard-ia"
    status = "Enabled"

    filter {
      and {
        prefix                   = var.object_prefix
        object_size_greater_than = var.minimum_object_size_bytes
      }
    }

    transition {
      days          = 0
      storage_class = "STANDARD_IA"
    }
  }
}
