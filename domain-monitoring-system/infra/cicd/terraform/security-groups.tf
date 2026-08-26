resource "aws_security_group" "jenkins_controller" {
  name        = "${var.project_name}-jenkins-controller-sg"
  description = "Access control for the Jenkins controller"
  vpc_id      = data.aws_vpc.default.id

  tags = {
    Name = "${var.project_name}-jenkins-controller-sg"
    Role = "jenkins-controller"
  }
}

resource "aws_security_group" "jenkins_agents" {
  name        = "${var.project_name}-jenkins-agents-sg"
  description = "Access control for the Jenkins Docker and Ansible agents"
  vpc_id      = data.aws_vpc.default.id

  tags = {
    Name = "${var.project_name}-jenkins-agents-sg"
    Role = "jenkins-agent"
  }
}

resource "aws_security_group" "alb" {
  name        = "${var.project_name}-alb-sg"
  description = "Public access to the application load balancer"
  vpc_id      = data.aws_vpc.default.id

  tags = {
    Name = "${var.project_name}-alb-sg"
    Role = "load-balancer"
  }
}

resource "aws_security_group" "production" {
  name        = "${var.project_name}-production-sg"
  description = "Access control for the production application servers"
  vpc_id      = data.aws_vpc.default.id

  tags = {
    Name = "${var.project_name}-production-sg"
    Role = "production"
  }
}

resource "aws_vpc_security_group_ingress_rule" "controller_ssh_from_admin" {
  security_group_id = aws_security_group.jenkins_controller.id
  description       = "Allow SSH from the administrator"
  cidr_ipv4         = var.admin_cidr
  from_port         = 22
  to_port           = 22
  ip_protocol       = "tcp"
}

resource "aws_vpc_security_group_ingress_rule" "controller_web_from_admin" {
  security_group_id = aws_security_group.jenkins_controller.id
  description       = "Allow Jenkins web access from the administrator"
  cidr_ipv4         = var.admin_cidr
  from_port         = 8080
  to_port           = 8080
  ip_protocol       = "tcp"
}

resource "aws_vpc_security_group_ingress_rule" "controller_web_from_agents" {
  security_group_id            = aws_security_group.jenkins_controller.id
  description                  = "Allow Jenkins agents to connect using WebSocket"
  referenced_security_group_id = aws_security_group.jenkins_agents.id
  from_port                    = 8080
  to_port                      = 8080
  ip_protocol                  = "tcp"
}

resource "aws_vpc_security_group_egress_rule" "controller_all_outbound" {
  security_group_id = aws_security_group.jenkins_controller.id
  description       = "Allow outbound access for updates and Git operations"
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}

resource "aws_vpc_security_group_ingress_rule" "agents_ssh_from_admin" {
  security_group_id = aws_security_group.jenkins_agents.id
  description       = "Allow SSH from the administrator"
  cidr_ipv4         = var.admin_cidr
  from_port         = 22
  to_port           = 22
  ip_protocol       = "tcp"
}

resource "aws_vpc_security_group_egress_rule" "agents_all_outbound" {
  security_group_id = aws_security_group.jenkins_agents.id
  description       = "Allow agents to reach Jenkins and download dependencies"
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}

resource "aws_vpc_security_group_ingress_rule" "alb_http_from_public" {
  security_group_id = aws_security_group.alb.id
  description       = "Allow public HTTP traffic"
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 80
  to_port           = 80
  ip_protocol       = "tcp"
}

resource "aws_vpc_security_group_egress_rule" "alb_to_production" {
  security_group_id            = aws_security_group.alb.id
  description                  = "Forward traffic to the production frontend"
  referenced_security_group_id = aws_security_group.production.id
  from_port                    = 5000
  to_port                      = 5000
  ip_protocol                  = "tcp"
}

resource "aws_vpc_security_group_ingress_rule" "production_frontend_from_alb" {
  security_group_id            = aws_security_group.production.id
  description                  = "Allow frontend traffic from the load balancer"
  referenced_security_group_id = aws_security_group.alb.id
  from_port                    = 5000
  to_port                      = 5000
  ip_protocol                  = "tcp"
}

resource "aws_vpc_security_group_ingress_rule" "production_ssh_from_admin" {
  security_group_id = aws_security_group.production.id
  description       = "Allow SSH from the administrator"
  cidr_ipv4         = var.admin_cidr
  from_port         = 22
  to_port           = 22
  ip_protocol       = "tcp"
}

resource "aws_vpc_security_group_ingress_rule" "production_ssh_from_ansible_agent" {
  security_group_id            = aws_security_group.production.id
  description                  = "Allow the Ansible Jenkins agent to deploy the application"
  referenced_security_group_id = aws_security_group.jenkins_agents.id
  from_port                    = 22
  to_port                      = 22
  ip_protocol                  = "tcp"
}

resource "aws_vpc_security_group_egress_rule" "production_all_outbound" {
  security_group_id = aws_security_group.production.id
  description       = "Allow image pulls, updates, and domain monitoring requests"
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}
