# Terraform Infrastructure - Baytak Foundation

## Overview

This Terraform project provisions the AWS infrastructure required to host the **Baytak Foundation Management System**.

Current infrastructure includes:

* Ubuntu 24.04 LTS EC2 Instance
* Security Group
* SSH Key Pair
* IAM Role
* IAM Instance Profile
* Automatic Ansible Inventory Generation

The EC2 instance will later be configured by **Ansible** to install:

* k3s
* Helm
* NGINX Ingress Controller
* cert-manager
* PostgreSQL
* FastAPI Backend
* React Frontend

---

# Project Structure

```text
terraform/
│
├── main.tf
├── variables.tf
├── terraform.tfvars
├── data.tf
├── key_pair.tf
├── security_group.tf
├── iam.tf
├── ec2.tf
├── outputs.tf
└── ansible_inventory.tpl
```

Each file has a single responsibility.

---

# How Terraform Works

Terraform follows a dependency graph rather than executing files in order.

```text
main.tf
    │
    ▼
variables.tf
    │
    ▼
terraform.tfvars
    │
    ▼
data.tf
    │
    ├──────────────┬───────────────┐
    ▼              ▼               ▼
key_pair.tf  security_group.tf   iam.tf
    └──────────────┬───────────────┘
                   ▼
                ec2.tf
                   ▼
              outputs.tf
                   ▼
      ansible_inventory.tpl
```

Terraform automatically determines the correct creation order based on resource references.

---

# main.tf

## Purpose

Configures Terraform itself.

It does **not** create any AWS resources.

Responsibilities:

* Define Terraform version
* Configure AWS Provider
* Select AWS Region

Example:

```hcl
provider "aws" {
  region = var.aws_region
}
```

Instead of hardcoding the region, the value comes from `variables.tf` and `terraform.tfvars`.

---

# variables.tf

## Purpose

Defines every configurable value used by the project.

Instead of writing values directly inside resources, Terraform references variables.

Example variable:

```hcl
variable "instance_type" {
  type = string
}
```

Example usage:

```hcl
instance_type = var.instance_type
```

Current variables include:

* AWS Region
* Instance Type
* Root Volume Size
* SSH CIDR
* Key Pair Name
* Project Name
* Environment

---

# terraform.tfvars

## Purpose

Provides actual values for variables.

Example:

```hcl
instance_type = "m7i-flex.large"

project_name = "baytak"

environment = "production"
```

Think of it as configuration for a specific environment.

Changing the EC2 type requires editing only this file.

---

# data.tf

## Purpose

Reads existing AWS resources.

Unlike `resource`, a `data` block never creates anything.

Current data sources:

### Ubuntu AMI

```hcl
data "aws_ami" "ubuntu"
```

Terraform automatically retrieves the latest Ubuntu 24.04 LTS image.

This avoids hardcoding an AMI ID.

---

### Default VPC

```hcl
data "aws_vpc" "default"
```

Reads the AWS default VPC.

---

### Default Subnets

```hcl
data "aws_subnets" "default"
```

Retrieves available subnet IDs inside the default VPC.

These values are later used by the EC2 resource.

---

# key_pair.tf

## Purpose

Uploads your **public SSH key** to AWS.

Terraform reads:

```text
~/.ssh/baytak.pub
```

using:

```hcl
public_key = file(var.public_key_path)
```

Only the public key is uploaded.

The private key always remains on your local computer.

The EC2 instance later references:

```hcl
key_name = aws_key_pair.baytak_key.key_name
```

which installs the public key into:

```text
/home/ubuntu/.ssh/authorized_keys
```

---

# security_group.tf

## Purpose

Acts as the EC2 firewall.

Current rules:

| Port | Protocol | Source   | Purpose |
| ---- | -------- | -------- | ------- |
| 22   | TCP      | Your IP  | SSH     |
| 80   | TCP      | Anywhere | HTTP    |
| 443  | TCP      | Anywhere | HTTPS   |

Example:

```hcl
ingress {

  from_port = 22

  to_port = 22

  protocol = "tcp"

  cidr_blocks = [
      var.ssh_cidr
  ]
}
```

Outbound traffic is unrestricted:

```hcl
protocol = "-1"
```

allowing software installation and package downloads.

---

# iam.tf

## Purpose

Creates an IAM identity for the EC2 instance.

Current resources:

* IAM Role
* IAM Instance Profile

No permissions are attached.

Current flow:

```text
EC2
 │
 ▼
Instance Profile
 │
 ▼
IAM Role
```

Later, if the server needs to access services like CloudWatch or ECR, permissions can be attached without recreating the EC2 instance.

---

# ec2.tf

## Purpose

Creates the Ubuntu production server.

This is the central resource in the project.

It combines:

* Ubuntu AMI
* Security Group
* Key Pair
* IAM Instance Profile

Example:

```hcl
ami = data.aws_ami.ubuntu.id
```

retrieves the latest Ubuntu image from `data.tf`.

Example:

```hcl
instance_type = var.instance_type
```

retrieves the instance type from `terraform.tfvars`.

Current EC2 configuration:

* Ubuntu 24.04 LTS
* m7i-flex.large
* gp3 encrypted root disk
* Detailed monitoring enabled
* IMDSv2 required
* Public IP assigned
* API termination protection enabled

Minimal bootstrap:

```bash
apt-get update -y

apt-get install -y python3 python3-pip
```

All additional software will be installed by Ansible.

---

# outputs.tf

## Purpose

Displays useful information after deployment.

Current outputs:

* Instance ID
* Public IP
* Public DNS
* Private IP

Example:

```hcl
output "public_ip" {

    value = aws_instance.baytak_server.public_ip

}
```

Instead of opening the AWS Console, Terraform prints these values after `terraform apply`.

---

# ansible_inventory.tpl

## Purpose

Automatically generates an Ansible inventory.

Example output:

```ini
[baytak]

18.198.xx.xx ansible_user=ubuntu ansible_ssh_private_key_file=~/.ssh/baytak

[baytak:vars]

ansible_python_interpreter=/usr/bin/python3
```

This allows Ansible to immediately connect to the newly created EC2 instance without manually editing an inventory file.

---

# Resource Relationships

The EC2 depends on several resources.

```text
Ubuntu AMI (data.tf)
        │
        ▼
     EC2 Instance
    ▲     ▲      ▲
    │     │      │
Key Pair  │  Security Group
           │
           ▼
   IAM Instance Profile
           │
           ▼
        IAM Role
```

Terraform automatically creates these resources in the correct order.

---

# Deployment Flow

```text
terraform init
        │
        ▼
terraform plan
        │
        ▼
terraform apply
        │
        ▼
AWS Infrastructure Created
        │
        ▼
Generate Ansible Inventory
        │
        ▼
ansible-playbook
        │
        ▼
Install k3s
Install Helm
Install Ingress Controller
Install cert-manager
Deploy Baytak Helm Chart
```

---

# Design Principles

This project follows several infrastructure best practices:

* Separate resources by responsibility.
* Store configurable values in `variables.tf` and `terraform.tfvars`.
* Use data sources instead of hardcoding AWS resource IDs.
* Use an IAM Role with no permissions until AWS access is actually required (principle of least privilege).
* Keep Terraform focused on infrastructure provisioning.
* Delegate server configuration and application deployment to Ansible.
* Use Helm as the single source of truth for Kubernetes resources.

This separation keeps the infrastructure easier to understand, maintain, and extend as the project grows.
