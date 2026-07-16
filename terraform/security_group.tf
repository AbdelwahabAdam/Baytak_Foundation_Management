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

  name        = "${var.project_name}-${var.environment}-sg"

  description = "Security Group for Baytak Production Server"

  vpc_id = data.aws_vpc.default.id

  #############################################################
  # SSH
  #############################################################

  ingress {

    description = "SSH"

    from_port = 22

    to_port = 22

    protocol = "tcp"

    cidr_blocks = [
      var.ssh_cidr
    ]

  }

  #############################################################
  # HTTP
  #############################################################

  ingress {

    description = "HTTP"

    from_port = 80

    to_port = 80

    protocol = "tcp"

    cidr_blocks = [
      "0.0.0.0/0"
    ]

  }

  #############################################################
  # HTTPS
  #############################################################

  ingress {

    description = "HTTPS"

    from_port = 443

    to_port = 443

    protocol = "tcp"

    cidr_blocks = [
      "0.0.0.0/0"
    ]

  }
#############################################################
# Kubernetes Ingress NodePort
#############################################################

ingress {

  description = "Kubernetes Ingress NodePort"

  from_port = 31019

  to_port = 31019

  protocol = "tcp"

  cidr_blocks = [
    "0.0.0.0/0"
  ]

}

  #############################################################
  # Outbound
  #############################################################

  egress {

    description = "Allow all outbound traffic"

    from_port = 0

    to_port = 0

    protocol = "-1"

    cidr_blocks = [
      "0.0.0.0/0"
    ]

  }

  #############################################################
  # Tags
  #############################################################

  tags = {

    Name = "${var.project_name}-${var.environment}-sg"

    Project = var.project_name

    Environment = var.environment

    ManagedBy = "Terraform"

  }

}