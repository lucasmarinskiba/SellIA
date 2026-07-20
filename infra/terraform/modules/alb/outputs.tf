output "dns_name" {
  value = aws_lb.main.dns_name
}

output "arn" {
  value = aws_lb.main.arn
}

output "backend_target_group_arn" {
  value = aws_lb_target_group.backend.arn
}

output "frontend_target_group_arn" {
  value = aws_lb_target_group.frontend.arn
}
