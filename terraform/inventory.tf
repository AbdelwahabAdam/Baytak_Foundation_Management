resource "local_file" "ansible_inventory" {
  filename = "${path.module}/../ansible/inventory.ini"

  content = templatefile("${path.module}/ansible_inventory.tpl", {
    public_ip = aws_instance.baytak_server.public_ip
  })
}