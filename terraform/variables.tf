variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "dev"
}

variable "s3_bucket_name" {
  description = "S3 telemetry bucket name"
  type        = string
  default     = "gridflow-tx-telemetry"
}

variable "instance_type" {
  description = "EC2 instance size"
  type        = string
  default     = "t3.micro"
}

variable "public_key" {
  description = "SSH public key for EC2 instance deployment"
  type        = string
  default     = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCym0ExpAkbEHFkvxo3egOVSmhhtVD7+K/MGzyBiwFAtWUNt+RzNkCDYagdSwxya5g4a9izwfKFd1q6aarHhmWsCDkAXwxXdOVYfW4SN73YcgyPztuoYdPY9ZIkGNztcQ/VBFyyn9ihMHtuKg5KQA+AKzB8S0zNLCT4w1fbJuukSiT+uBExHs/ZibJrVzw8Bh+u61Hu4u2zMgL8njQRNNytf2qBt4G6qkAxPfT2xs+xND/Tky47D96WsEAAhhzGCMngKekANgAlR7cwv5KqVBQVaw8MsHf6h1mXaQpm0eFfPKf2cJLHCCVByHOLvdTDWWMrNE8uHejiN06nfZEIS+MR"
}

