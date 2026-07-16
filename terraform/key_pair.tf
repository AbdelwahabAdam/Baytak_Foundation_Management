###############################################################
# key_pair.tf
#
# Uploads your LOCAL public SSH key to AWS.
#
# IMPORTANT:
# Terraform uploads ONLY the PUBLIC key.
#
# Your private key NEVER leaves your computer.
###############################################################

resource "aws_key_pair" "baytak_key" {

  #############################################################
  # Name of the Key Pair inside AWS.
  #
  # This is the name you'll see in the EC2 Console.
  #############################################################

  key_name = var.key_pair_name

  #############################################################
  # Read the local public key file.
  #
  # Example:
  #
  # ~/.ssh/baytak.pub
  #############################################################

  public_key = file(var.public_key_path)

  #############################################################
  # Resource Tags
  #############################################################

  tags = {

    Name = "${var.project_name}-keypair"

    Project = var.project_name

    Environment = var.environment

    ManagedBy = "Terraform"

  }

}