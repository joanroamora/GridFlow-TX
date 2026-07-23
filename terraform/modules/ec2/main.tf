data "aws_ami" "amazon_linux_2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_security_group" "ec2_sg" {
  name        = "gridflow-ec2-sg-${var.environment}"
  description = "Security Group for GridFlow-TX EC2 instance (SSH, HTTP, Streamlit)"
  vpc_id      = var.vpc_id

  # SSH Access
  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTP Access
  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Streamlit GUI Port
  ingress {
    description = "Streamlit GUI"
    from_port   = 8501
    to_port     = 8501
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Outbound rule
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "gridflow-ec2-sg-${var.environment}"
    Environment = var.environment
    Project     = "GridFlow-TX"
  }
}

resource "aws_key_pair" "app_key" {
  count      = var.public_key != "" ? 1 : 0
  key_name   = "gridflow-ec2-key-${var.environment}"
  public_key = var.public_key
}

resource "aws_instance" "app_node" {
  ami                    = data.aws_ami.amazon_linux_2023.id
  instance_type          = var.instance_type
  subnet_id              = var.subnet_id
  vpc_security_group_ids = [aws_security_group.ec2_sg.id]
  key_name               = var.public_key != "" ? aws_key_pair.app_key[0].key_name : (var.key_name != "" ? var.key_name : null)

  root_block_device {
    volume_size           = 8
    volume_type           = "gp3"
    encrypted             = true
    delete_on_termination = true
  }

  tags = {
    Name        = "gridflow-ec2-${var.environment}"
    Environment = var.environment
    Project     = "GridFlow-TX"
  }
}

# Elastic IP for persistent public IP address
resource "aws_eip" "app_eip" {
  domain   = "vpc"
  instance = aws_instance.app_node.id

  tags = {
    Name        = "gridflow-eip-${var.environment}"
    Environment = var.environment
    Project     = "GridFlow-TX"
  }
}
