output "instance_id" {
  description = "ID of the EC2 instance"
  value       = aws_instance.app_node.id
}

output "public_ip" {
  description = "Public Elastic IP of the EC2 instance"
  value       = aws_eip.app_eip.public_ip
}

output "security_group_id" {
  description = "Security Group ID of the EC2 instance"
  value       = aws_security_group.ec2_sg.id
}
