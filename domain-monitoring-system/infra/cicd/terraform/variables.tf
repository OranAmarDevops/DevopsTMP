variable "aws_region" {
  description = "AWS region where the infrastructure will be created"
  type        = string
  default     = "eu-central-1"
}

variable "project_name" {
  description = "Project name used in resource names and tags"
  type        = string
  default     = "domain-monitoring-system"
}

variable "instance_type" {
  description = "EC2 instance type used by the exercise servers"
  type        = string
  default     = "t3.micro"
}

variable "key_name" {
  description = "Name of the existing AWS EC2 key pair"
  type        = string
  default     = "docker-swarm-key"
}

variable "admin_cidr" {
  description = "Public administrator IP address allowed to connect by SSH"
  type        = string

  validation {
    condition     = can(cidrnetmask(var.admin_cidr))
    error_message = "admin_cidr must be a valid IPv4 CIDR, for example 1.2.3.4/32."
  }
}

variable "production_instance_count" {
  description = "Number of production application servers"
  type        = number
  default     = 2
}