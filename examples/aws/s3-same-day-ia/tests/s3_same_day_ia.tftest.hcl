mock_provider "aws" {
  mock_resource "aws_s3_bucket" {
    defaults = {
      arn = "arn:aws:s3:::infrastructure-curiosity-same-day-ia-test"
      id  = "infrastructure-curiosity-same-day-ia-test"
    }
  }
}

run "plans_a_same_day_standard_ia_transition" {
  command = plan

  variables {
    region                    = "us-east-1"
    bucket_name               = "infrastructure-curiosity-same-day-ia-test"
    object_prefix             = "immutable-backups/"
    minimum_object_size_bytes = 128000
  }

  assert {
    condition     = aws_s3_bucket_lifecycle_configuration.archive.region == "us-east-1"
    error_message = "The lifecycle configuration must use the bucket's resource-level Region."
  }

  assert {
    condition     = one(aws_s3_bucket_lifecycle_configuration.archive.rule[0].transition).days == 0
    error_message = "The lifecycle transition must be eligible on day zero."
  }

  assert {
    condition     = one(aws_s3_bucket_lifecycle_configuration.archive.rule[0].transition).storage_class == "STANDARD_IA"
    error_message = "The day-zero destination must be S3 Standard-IA."
  }

  assert {
    condition     = aws_s3_bucket_lifecycle_configuration.archive.rule[0].filter[0].and[0].object_size_greater_than == 128000
    error_message = "The rule must exclude objects of 128 KB or less from transition."
  }

  assert {
    condition = (
      aws_s3_bucket_public_access_block.archive.block_public_acls &&
      aws_s3_bucket_public_access_block.archive.block_public_policy &&
      aws_s3_bucket_public_access_block.archive.ignore_public_acls &&
      aws_s3_bucket_public_access_block.archive.restrict_public_buckets
    )
    error_message = "The example bucket must retain all public-access blocks."
  }

  assert {
    condition     = output.same_day_transition.minimum_billable_duration_days == 30
    error_message = "The summary must preserve the separate 30-day minimum billing caveat."
  }
}

run "rejects_a_small_object_threshold_below_128_kb" {
  command = plan

  variables {
    minimum_object_size_bytes = 127999
  }

  expect_failures = [var.minimum_object_size_bytes]
}

run "rejects_an_invalid_bucket_name" {
  command = plan

  variables {
    bucket_name = "Invalid_Bucket_Name"
  }

  expect_failures = [var.bucket_name]
}
