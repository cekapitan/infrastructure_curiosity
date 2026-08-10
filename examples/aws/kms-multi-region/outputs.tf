output "related_key_arns" {
  description = "Regional ARNs for the primary and replica. Related keys share key material and a key ID, but not an ARN."
  value = {
    (var.primary_region) = aws_kms_key.primary.arn
    (var.replica_region) = aws_kms_replica_key.replica.arn
  }
}

output "regional_aliases" {
  description = "Same alias name managed independently in each Region."
  value = {
    (var.primary_region) = aws_kms_alias.primary.name
    (var.replica_region) = aws_kms_alias.replica.name
  }
}
