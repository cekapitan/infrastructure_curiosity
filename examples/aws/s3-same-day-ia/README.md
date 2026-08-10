# Amazon S3 same-day Standard-IA transition

Status: **new in the current window**. On July 16, 2026, AWS removed the rule that required objects to remain in S3 Standard for 30 days before S3 Lifecycle could transition them to S3 Standard-IA or S3 One Zone-IA. New rules can make objects eligible on day 0.

This test-only Terraform example uses AWS provider v6.58.0 and sets `transition.days = 0` explicitly. It applies the rule only to a chosen prefix and objects larger than 128,000 bytes, while keeping the provider's default 128 KB transition floor explicit. The bucket shape also blocks public access and selects SSE-S3 encryption.

## What did not change

The launch removed the **waiting period before transition**. It did not remove Standard-IA economics:

- Standard-IA still has a 30-day minimum billable storage duration. Deleting, overwriting, or transitioning an object out sooner can charge the remaining days.
- Standard-IA still has a 128 KB minimum billable object size and retrieval fees.
- Each object transition incurs a Lifecycle transition request charge. Many small objects can cost more to transition than they save.
- Lifecycle actions are asynchronous. `days = 0` makes an object eligible on the day it is created; it does not promise an immediate physical move.
- Use S3 Intelligent-Tiering instead when access patterns are unknown or change over time, after comparing monitoring, request, retrieval, and storage costs.

The current S3 User Guide page retrieved during this review still contains the superseded statement that Standard-IA transitions require 30 days. The dated July 16, 2026 AWS announcement is the authoritative source for the newly allowed day-zero transition. Keep this documentation lag in mind when reviewing policies or provider diagnostics.

`object_size_greater_than` is exclusive. With the default `128000`, an object must be larger than 128,000 bytes to match this rule.

## Offline validation only

The test supplies a mocked AWS provider and every run uses `command = plan`. It does not read credentials, contact AWS, create state remotely, or provision a bucket.

```bash
terraform fmt -check -recursive
terraform init -backend=false
terraform validate
terraform test
```

Do not run `apply` or `destroy` from this repository.

## First-party references

- [AWS announcement - July 16, 2026](https://aws.amazon.com/about-aws/whats-new/2026/07/s3-removes-30-day-transitions-standard-ia-one-zone-ia)
- [S3 Lifecycle transition considerations](https://docs.aws.amazon.com/AmazonS3/latest/userguide/lifecycle-transition-general-considerations.html)
- [S3 storage-class economics](https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage-class-intro.html)
- [Amazon S3 pricing](https://aws.amazon.com/s3/pricing/)
- [Terraform AWS provider lifecycle resource](https://registry.terraform.io/providers/hashicorp/aws/6.58.0/docs/resources/s3_bucket_lifecycle_configuration)
