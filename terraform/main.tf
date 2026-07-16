###############################################################
# main.tf
#
# Terraform configuration
###############################################################

terraform {

  required_version = ">= 1.8"

  required_providers {

    aws = {

      source = "hashicorp/aws"

      version = "~> 6.0"

    }

    local = {
      source = "hashicorp/local"
    }
  }

}

###############################################################
# AWS Provider
###############################################################

provider "aws" {

  region = var.aws_region

}