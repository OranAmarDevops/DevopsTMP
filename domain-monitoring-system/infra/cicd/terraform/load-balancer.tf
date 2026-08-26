resource "aws_lb" "application_lb" {
  name               = "dms-application-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = data.aws_subnets.default.ids

  enable_deletion_protection = false

  tags = {
    Name        = "${var.project_name}-alb"
    Role        = "load-balancer"
    Environment = "production"
  }
}

resource "aws_lb_target_group" "frontend" {
  name        = "dms-frontend-tg"
  port        = 5000
  protocol    = "HTTP"
  vpc_id      = data.aws_vpc.default.id
  target_type = "instance"

  deregistration_delay = 30

  health_check {
    enabled             = true
    path                = "/health"
    protocol            = "HTTP"
    port                = "traffic-port"
    matcher             = "200-399"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
  }

  stickiness {
    enabled         = true
    type            = "lb_cookie"
    cookie_duration = 1800
  }

  tags = {
    Name        = "${var.project_name}-frontend-tg"
    Environment = "production"
  }
}

resource "aws_lb_target_group_attachment" "production" {
  count = var.production_instance_count

  target_group_arn = aws_lb_target_group.frontend.arn
  target_id        = aws_instance.production[count.index].id
  port             = 5000
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.application_lb.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.frontend.arn
  }
}