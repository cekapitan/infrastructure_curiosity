variable "region" {
  description = "AWS Region for the test-only bucket configuration."
  type        = string
  default     = "us-east-1"

  validation {
    condition     = can(regex("^[a-z]{2}(-[a-z0-9]+)+-[0-9]+$", var.region))
    error_message = "region must look like an AWS Region identifier."
  }
}

variable "bucket_name" {
  description = "Globally unique S3 bucket name if this example is adapted elsewhere."
  type        = string
  default     = "infrastructure-curiosity-same-day-ia-example"

  validation {
    condition = (
      length(var.bucket_name) >= 3 &&
      length(var.bucket_name) <= 63 &&
      can(regex("^[a-z0-9][a-z0-9.-]*[a-z0-9]$", var.bucket_name)) &&
      !strcontains(var.bucket_name, "..") &&
      !can(regex("^[0-9]+\\.[0-9]+\\.[0-9]+\\.[0-9]+$", var.bucket_name))
    )
    error_message = "bucket_name must be a valid 3-63 character general-purpose S3 bucket name."
  }
}

variable "object_prefix" {
  description = "Key prefix containing objects that become cold immediately; an empty string selects the whole bucket."
  type        = string
  default     = "backups/"

  validation {
    condition     = !startswith(var.object_prefix, "/")
    error_message = "object_prefix must be an S3 key prefix without a leading slash."
  }
}

variable "minimum_object_size_bytes" {
  description = "Exclusive lower bound for objects eligible to transition. The default keeps objects of 128 KB or less in S3 Standard."
  type        = number
  default     = 128000

  validation {
    condition = (
      var.minimum_object_size_bytes >= 128000 &&
      floor(var.minimum_object_size_bytes) == var.minimum_object_size_bytes
    )
    error_message = "minimum_object_size_bytes must be an integer of at least 128000 bytes."
  }
}

variable "tags" {
  description = "Tags applied to the bucket."
  type        = map(string)
  default = {
    ManagedBy = "Terraform"
    Purpose   = "infrastructure-curiosity"
  }
}
