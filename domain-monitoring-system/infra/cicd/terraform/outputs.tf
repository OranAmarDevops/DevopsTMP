output "jenkins_controller_public_ip" {
  description = "Public IP address of the Jenkins controller"
  value       = aws_instance.jenkins_controller.public_ip
}

output "jenkins_url" {
  description = "URL of the Jenkins web interface"
  value       = "http://${aws_instance.jenkins_controller.public_ip}:8080"
}

output "docker_agent_public_ip" {
  description = "Public IP address of the Jenkins Docker agent"
  value       = aws_instance.docker_agent.public_ip
}

output "ansible_agent_public_ip" {
  description = "Public IP address of the Jenkins Ansible agent"
  value       = aws_instance.ansible_agent.public_ip
}

output "production_public_ips" {
  description = "Public IP addresses of the production servers"
  value       = aws_instance.production[*].public_ip
}

output "production_private_ips" {
  description = "Private IP addresses used by the Ansible agent"
  value       = aws_instance.production[*].private_ip
}

output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = aws_lb.application_lb.dns_name
}

output "application_url" {
  description = "Public URL of the monitoring application"
  value       = "http://${aws_lb.application_lb.dns_name}"
}

output "default_vpc_id" {
  description = "ID of the default VPC used by the infrastructure"
  value       = data.aws_vpc.default.id
}

output "default_subnet_ids" {
  description = "Default subnet IDs used by the infrastructure"
  value       = data.aws_subnets.default.ids
}