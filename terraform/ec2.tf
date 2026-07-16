###############################################################
# ec2.tf
#
# Creates the production Ubuntu EC2 instance.
###############################################################

resource "aws_instance" "baytak_server" {

  #############################################################
  # Ubuntu 24.04 LTS
  #############################################################

  ami = data.aws_ami.ubuntu.id

  #############################################################
  # Instance Type
  #############################################################

  instance_type = var.instance_type

  #############################################################
  # SSH Key Pair
  #############################################################

  key_name = aws_key_pair.baytak_key.key_name


  #############################################################
  # Networking
  #############################################################

  subnet_id = data.aws_subnets.default.ids[0]

  vpc_security_group_ids = [

    aws_security_group.baytak_sg.id

  ]

  associate_public_ip_address = true

  #############################################################
  # IAM
  #############################################################

  iam_instance_profile = aws_iam_instance_profile.ec2_profile.name

  #############################################################
  # Root Disk
  #############################################################

  root_block_device {

    volume_size = var.root_volume_size

    volume_type = var.root_volume_type

    encrypted = true

    delete_on_termination = true

  }

  #############################################################
  # Enable Detailed Monitoring
  #############################################################

  monitoring = true

  #############################################################
  # Prevent accidental termination
  #############################################################

  disable_api_termination = false

  #############################################################
  # Shutdown behavior
  #############################################################

  instance_initiated_shutdown_behavior = "stop"

  #############################################################
  # Force IMDSv2
  #############################################################

  metadata_options {

    http_endpoint = "enabled"

    http_tokens = "required"

  }

  #############################################################
  # Minimal bootstrap
  #############################################################

  user_data = <<-EOF
#!/bin/bash

apt-get update -y

apt-get install -y python3 python3-pip

EOF

  #############################################################
  # Tags
  #############################################################

  tags = {

    Name = "${var.project_name}-${var.environment}"

    Project = var.project_name

    Environment = var.environment

    ManagedBy = "Terraform"

  }

}

resource "local_file" "instance_ip" {
  filename = "${path.module}/../instance_ip"
  content  = aws_instance.baytak_server.public_ip
}