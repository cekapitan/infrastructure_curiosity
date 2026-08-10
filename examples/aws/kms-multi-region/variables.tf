variable "primary_region" {
  description = "AWS Region that owns the multi-Region primary key."
  type        = string
  default     = "us-east-1"

  validation {
    condition     = can(regex("^[a-z]{2}(-[a-z0-9]+)+-[0-9]+$", var.primary_region))
    error_message = "primary_region must look like an AWS Region identifier."
  }
}

variable "replica_region" {
  description = "Different AWS Region that owns the replica key."
  type        = string
  default     = "us-west-2"

  validation {
    condition     = can(regex("^[a-z]{2}(-[a-z0-9]+)+-[0-9]+$", var.replica_region))
    error_message = "replica_region must look like an AWS Region identifier."
  }
}

variable "alias_name" {
  description = "Regional alias name assigned independently to both related keys."
  type        = string
  default     = "alias/infrastructure-curiosity"

  validation {
    condition = (
      can(regex("^alias/[A-Za-z0-9/_-]+$", var.alias_name)) &&
      !startswith(var.alias_name, "alias/aws/")
    )
    error_message = "alias_name must start with alias/, use valid alias characters, and not use the reserved alias/aws/ prefix."
  }
}

variable "description" {
  description = "Base description applied to the primary key and replica."
  type        = string
  default     = "Infrastructure Curiosity multi-Region application key"

  validation {
    condition     = length(trimspace(var.description)) > 0
    error_message = "description must not be empty."
  }
}

variable "tags" {
  description = "Tags copied deliberately to each regional key; KMS does not synchronize tags."
  type        = map(string)
  default = {
    ManagedBy = "Terraform"
    Purpose   = "infrastructure-curiosity"
  }
}
