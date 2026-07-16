###############################################################
# data.tf
#
# Data sources retrieve information from AWS.
#
# Unlike resources, data sources DO NOT create anything.
#
# They simply query existing AWS resources.
###############################################################



###############################################################
# Latest Ubuntu 24.04 LTS AMI
#
# Instead of hardcoding an AMI ID,
# Terraform always finds the newest official Ubuntu image.
#
# Canonical owns all official Ubuntu AMIs.
###############################################################

data "aws_ami" "ubuntu" {

  #############################################################
  # Always choose the newest matching image.
  #############################################################

  most_recent = true

  #############################################################
  # Canonical (Ubuntu) AWS Account ID
  #############################################################

  owners = ["099720109477"]

  #############################################################
  # Filter by image name
  #############################################################

  filter {

    name = "name"

    values = [
      "ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"
    ]

  }

  #############################################################
  # Only HVM virtualization
  #############################################################

  filter {

    name = "virtualization-type"

    values = ["hvm"]

  }

}

data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}