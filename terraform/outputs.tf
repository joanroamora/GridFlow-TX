output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "ec2_public_ip" {
  description = "Public IP of the EC2 Instance"
  value       = module.ec2.public_ip
}

output "s3_bucket_arn" {
  description = "ARN of the Telemetry S3 Bucket"
  value       = module.s3.bucket_arn
}
