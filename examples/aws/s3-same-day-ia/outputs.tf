output "bucket_arn" {
  description = "ARN of the bucket receiving the Lifecycle configuration."
  value       = aws_s3_bucket.archive.arn
}

output "same_day_transition" {
  description = "Review-friendly summary of the transition policy."
  value = {
    region                         = var.region
    prefix                         = var.object_prefix
    transition_after_days          = 0
    storage_class                  = "STANDARD_IA"
    object_size_greater_than_bytes = var.minimum_object_size_bytes
    minimum_billable_duration_days = 30
  }
}
