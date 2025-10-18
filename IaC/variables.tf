variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "eu-central-1"
}

variable "project_name" {
  description = "Project name prefix"
  type        = string
  default     = "teklo-card-ml"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "prod"
}

variable "training_instance_type" {
  description = "SageMaker training instance type"
  type        = string
  default     = "ml.m5.large"
}

variable "batch_max_vcpus" {
  description = "Maximum vCPUs for batch compute environment"
  type        = number
  default     = 10
}
