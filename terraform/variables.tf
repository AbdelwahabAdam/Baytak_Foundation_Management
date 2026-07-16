###############################################################
# variables.tf
#
# This file defines all configurable values used throughout
# the Terraform project.
#
# Benefits:
# - Easier to maintain
# - Easier to reuse
# - Avoids hardcoded values
###############################################################

###############################################################
# AWS Region
###############################################################

variable "aws_region" {

  description = "AWS region where resources will be created."

  type = string

  default = "eu-central-1"

}

###############################################################
# Project Name
###############################################################

variable "project_name" {

  description = "Project name used in resource naming."

  type = string

  default = "baytak"

}

###############################################################
# Environment
###############################################################

variable "environment" {

  description = "Deployment environment."

  type = string

  default = "production"

}

###############################################################
# EC2 Instance Type
###############################################################

variable "instance_type" {

  description = "EC2 instance type."

  type = string

  default = "m7i-flex.large"

}

###############################################################
# Root Volume Size
###############################################################

variable "root_volume_size" {

  description = "Root EBS volume size in GB."

  type = number

  default = 30

}

###############################################################
# Root Volume Type
###############################################################

variable "root_volume_type" {

  description = "Root EBS volume type."

  type = string

  default = "gp3"

}

###############################################################
# EC2 Key Pair Name
###############################################################

variable "key_pair_name" {

  description = "AWS EC2 Key Pair name."

  type = string

}

###############################################################
# Local Public Key
###############################################################

variable "public_key_path" {

  description = "Path to the local SSH public key."

  type = string

}

###############################################################
# Allowed SSH CIDR
###############################################################

variable "ssh_cidr" {

  description = "CIDR allowed to SSH into the EC2 instance."

  type = string

}