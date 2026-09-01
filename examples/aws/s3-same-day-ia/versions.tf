terraform {
  required_version = ">= 1.7.0, < 2.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "6.62.0"
    }
  }
}

# The resources select their Region directly through AWS provider v6. The
# default also names that Region for provider-wide operations.
provider "aws" {
  region = var.region
}
