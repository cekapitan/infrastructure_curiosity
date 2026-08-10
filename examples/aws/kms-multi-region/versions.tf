terraform {
  required_version = ">= 1.7.0, < 2.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "= 6.58.0"
    }
  }
}

# Every resource selects its Region directly. The default still names a Region
# for provider-wide operations, but AWS provider v6 needs no aliases here.
provider "aws" {
  region = var.primary_region
}
