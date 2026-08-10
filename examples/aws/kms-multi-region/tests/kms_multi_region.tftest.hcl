mock_provider "aws" {
  mock_resource "aws_kms_key" {
    defaults = {
      arn    = "arn:aws:kms:us-east-1:111122223333:key/mrk-1234567890abcdef1234567890abcdef"
      key_id = "mrk-1234567890abcdef1234567890abcdef"
    }
  }

  mock_resource "aws_kms_replica_key" {
    defaults = {
      arn    = "arn:aws:kms:us-west-2:111122223333:key/mrk-1234567890abcdef1234567890abcdef"
      key_id = "mrk-1234567890abcdef1234567890abcdef"
    }
  }
}

run "plans_related_keys_in_distinct_regions" {
  command = plan

  variables {
    primary_region = "us-east-1"
    replica_region = "us-west-2"
    alias_name     = "alias/team-data"
  }

  assert {
    condition     = aws_kms_key.primary.region == "us-east-1"
    error_message = "The primary key must use the resource-level primary Region."
  }

  assert {
    condition     = aws_kms_key.primary.multi_region && aws_kms_key.primary.enable_key_rotation
    error_message = "The primary key must be multi-Region with automatic rotation enabled."
  }

  assert {
    condition     = aws_kms_replica_key.replica.region == "us-west-2"
    error_message = "The replica must use the resource-level replica Region."
  }

  assert {
    condition = (
      aws_kms_alias.primary.name == "alias/team-data" &&
      aws_kms_alias.replica.name == "alias/team-data" &&
      aws_kms_alias.primary.region != aws_kms_alias.replica.region
    )
    error_message = "The same alias name must be managed independently in both Regions."
  }

  assert {
    condition     = aws_kms_key.primary.tags["RegionRole"] == "primary" && aws_kms_replica_key.replica.tags["RegionRole"] == "replica"
    error_message = "Independent regional tags must identify the primary and replica roles."
  }
}

run "rejects_a_replica_in_the_primary_region" {
  command = plan

  variables {
    primary_region = "us-east-1"
    replica_region = "us-east-1"
  }

  expect_failures = [aws_kms_replica_key.replica]
}

run "rejects_reserved_aws_aliases" {
  command = plan

  variables {
    alias_name = "alias/aws/not-ours"
  }

  expect_failures = [var.alias_name]
}
