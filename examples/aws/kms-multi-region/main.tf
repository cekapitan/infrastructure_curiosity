resource "aws_kms_key" "primary" {
  region = var.primary_region

  description                        = "${var.description} (primary in ${var.primary_region})"
  customer_master_key_spec           = "SYMMETRIC_DEFAULT"
  key_usage                          = "ENCRYPT_DECRYPT"
  multi_region                       = true
  enable_key_rotation                = true
  deletion_window_in_days            = 30
  bypass_policy_lockout_safety_check = false

  tags = merge(var.tags, {
    RegionRole = "primary"
  })

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_kms_replica_key" "replica" {
  region = var.replica_region

  description             = "${var.description} (replica in ${var.replica_region})"
  primary_key_arn         = aws_kms_key.primary.arn
  deletion_window_in_days = 30
  enabled                 = true

  tags = merge(var.tags, {
    RegionRole = "replica"
  })

  lifecycle {
    prevent_destroy = true

    precondition {
      condition     = var.primary_region != var.replica_region
      error_message = "replica_region must differ from primary_region."
    }
  }
}

# Aliases are independent regional resources. Reusing the same name is valid
# because each alias targets the related key in its own Region.
resource "aws_kms_alias" "primary" {
  region = var.primary_region

  name          = var.alias_name
  target_key_id = aws_kms_key.primary.key_id
}

resource "aws_kms_alias" "replica" {
  region = var.replica_region

  name          = var.alias_name
  target_key_id = aws_kms_replica_key.replica.key_id
}
