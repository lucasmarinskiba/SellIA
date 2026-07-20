output "repository_url" {
  description = "URL del repositorio ECR para el sidecar"
  value       = aws_ecr_repository.sidecar.repository_url
}

output "repository_arn" {
  description = "ARN del repositorio ECR para el sidecar"
  value       = aws_ecr_repository.sidecar.arn
}
