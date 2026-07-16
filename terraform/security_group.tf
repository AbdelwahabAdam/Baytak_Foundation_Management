###############################################################
# security_group.tf
#
# Security Group for the Baytak Production Server
#
# Allows:
# - SSH (22) only from your IP
# - HTTP (80) from anywhere
# - HTTPS (443) from anywhere
#
# Allows all outbound traffic.
###############################################################

resource "aws_security_group" "baytak_sg" {
  name        = "baytak-sg"
  description = "Security group for Baytak server"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Application HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Application HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Ingress NGINX HTTP NodePort"
    from_port   = 31080
    to_port     = 31080
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Ingress NGINX HTTPS NodePort"
    from_port   = 31443
    to_port     = 31443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "baytak-sg"
  }
}