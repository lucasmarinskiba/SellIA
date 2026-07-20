# ============================================================
# Sidecar Module — ECR Repository + IAM
# ============================================================

resource "aws_ecr_repository" "sidecar" {
  name                 = "${var.project_name}-sidecar"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = {
    Name        = "${var.project_name}-sidecar"
    Environment = var.environment
  }
}

resource "aws_ecr_lifecycle_policy" "sidecar" {
  repository = aws_ecr_repository.sidecar.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 30 images"
        selection = {
          tagStatus     = "any"
          countType     = "imageCountMoreThan"
          countNumber   = 30
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}
