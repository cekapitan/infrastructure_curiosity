# AWS KMS multi-Region keys

Status: **established capability, newly cataloged**. AWS launched multi-Region keys on June 16, 2021. This is useful infrastructure, but it is not a 2026 release.

This test-only Terraform example creates the shape of one multi-Region primary key and one replica. AWS provider v6's resource-level `region` argument keeps both Regions in one provider configuration instead of requiring provider aliases. The primary enables automatic rotation, both keys have a 30-day deletion window, and `prevent_destroy` adds a review barrier.

The same alias is created separately in each Region to make an important boundary visible: related keys share key material and a key ID, but each key has its own ARN, key policy, grants, aliases, tags, description, and enabled state. The example intentionally copies tags and alias names rather than implying AWS KMS synchronizes them.

## Good fits

- Client-side encryption that must decrypt in another Region without a cross-Region KMS call.
- Active-active applications using the AWS Encryption SDK or compatible client-side encryption libraries.
- Disaster recovery, backup, and signing workflows that genuinely require identical key material.

Most AWS services that use KMS for encryption at rest still treat a related multi-Region key like a regional key. For example, S3 cross-Region replication still decrypts and re-encrypts data keys in the destination Region. Do not adopt multi-Region keys merely to avoid managing ordinary regional service keys.

## Security and operations caveats

- Key policies and grants are regional and are not synchronized. This example leaves `policy` unset so AWS KMS applies its default API policy; a production module should use separately reviewed policies for every Region.
- Restrict `kms:ReplicateKey`, `kms:CreateKey`, and allowed replica Regions. Creating the first multi-Region key can also require permission for the KMS service-linked role.
- `prevent_destroy` only helps while the resource remains in configuration. It is not a substitute for IAM controls, separation of duties, or deletion alarms.
- A replica must be in a different Region in the same AWS partition, and only one replica of a primary can exist per Region.
- Automatic rotation is configured on the primary because rotation is a synchronized property of the related keys.
- Existing single-Region keys cannot be converted, related keys are billed and counted against quotas separately, and custom key stores do not support multi-Region keys.
- Replication transfers key material across a Region boundary inside AWS KMS. Confirm data-residency and regulatory requirements before adopting it.

## Offline validation only

The test supplies a mocked AWS provider and every run uses `command = plan`. It does not read credentials, contact AWS, create state remotely, or provision a key.

```bash
terraform fmt -check -recursive
terraform init -backend=false
terraform validate
terraform test
```

Do not run `apply` or `destroy` from this repository.

## First-party references

- [AWS launch announcement - June 16, 2021](https://aws.amazon.com/about-aws/whats-new/2021/06/kms-multi-region-keys/)
- [AWS KMS multi-Region key overview](https://docs.aws.amazon.com/kms/latest/developerguide/multi-region-keys-overview.html)
- [How related keys work](https://docs.aws.amazon.com/kms/latest/developerguide/mrk-how-it-works.html)
- [Authorization boundaries for related keys](https://docs.aws.amazon.com/kms/latest/developerguide/multi-region-keys-auth.html)
- [HashiCorp AWS provider per-resource Region override](https://developer.hashicorp.com/terraform/tutorials/configuration-language/configure-providers#per-resource-region-override-with-the-aws-provider)
