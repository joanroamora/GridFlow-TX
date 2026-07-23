variable "bucket_name" {
  description = "Name of the S3 bucket"
  type        = string
  default     = "gridflow-tx-telemetry"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}
