###############################################################
# outputs.tf
###############################################################

output "instance_id" {

  description = "EC2 Instance ID"

  value = aws_instance.baytak_server.id

}

output "public_ip" {

  description = "EC2 Public IP"

  value = aws_instance.baytak_server.public_ip

}

output "public_dns" {

  description = "EC2 Public DNS"

  value = aws_instance.baytak_server.public_dns

}

output "private_ip" {

  description = "EC2 Private IP"

  value = aws_instance.baytak_server.private_ip

}

output "master_ip" {
  value = aws_instance.baytak_server.public_ip
}