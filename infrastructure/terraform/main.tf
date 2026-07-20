"""
Terraform — Infrastructure as Code para producción.

Deploy: terraform init && terraform apply
"""

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# ========== VPC + Networking ==========

resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
  tags = {
    Name = "sellia-vpc"
  }
}

resource "aws_subnet" "public" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 1}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]
  tags = {
    Name = "sellia-public-${count.index + 1}"
  }
}

resource "aws_subnet" "private" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 101}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]
  tags = {
    Name = "sellia-private-${count.index + 1}"
  }
}

# ========== EKS Cluster ==========

resource "aws_eks_cluster" "main" {
  name            = "sellia-cluster"
  role_arn        = aws_iam_role.eks_cluster.arn
  version         = "1.28"
  vpc_config {
    subnet_ids = concat(aws_subnet.public[*].id, aws_subnet.private[*].id)
  }
}

resource "aws_eks_node_group" "main" {
  cluster_name    = aws_eks_cluster.main.name
  node_group_name = "sellia-nodes"
  node_role_arn   = aws_iam_role.eks_node.arn
  subnet_ids      = aws_subnet.private[*].id

  scaling_config {
    desired_size = 3
    max_size     = 20
    min_size     = 2
  }

  instance_types = ["t3.large"]
  disk_size      = 50

  tags = {
    Name = "sellia-nodes"
  }
}

# ========== RDS Database ==========

resource "aws_db_instance" "main" {
  identifier     = "sellia-db"
  engine         = "postgres"
  engine_version = "15.3"
  instance_class = "db.t3.medium"

  db_name  = "sellia"
  username = "postgres"
  password = var.db_password  # Use secrets manager in prod

  allocated_storage = 100
  multi_az          = true
  storage_encrypted = true

  backup_retention_period = 30
  publicly_accessible     = false
  skip_final_snapshot     = false
  final_snapshot_identifier = "sellia-final-snapshot-${formatdate("YYYY-MM-DD-hhmmss", timestamp())}"

  tags = {
    Name = "sellia-db"
  }
}

# ========== ElastiCache Redis ==========

resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "sellia-redis"
  engine               = "redis"
  node_type           = "cache.t3.medium"
  num_cache_nodes      = 3
  parameter_group_name = "default.redis7"
  engine_version       = "7.0"
  port                 = 6379
  automatic_failover_enabled = true

  tags = {
    Name = "sellia-redis"
  }
}

# ========== S3 Buckets ==========

resource "aws_s3_bucket" "images" {
  bucket = "sellia-images-${data.aws_caller_identity.current.account_id}"
  tags = {
    Name = "sellia-images"
  }
}

resource "aws_s3_bucket_versioning" "images" {
  bucket = aws_s3_bucket.images.id
  versioning_configuration {
    status = "Enabled"
  }
}

# ========== IAM Roles ==========

resource "aws_iam_role" "eks_cluster" {
  name = "sellia-eks-cluster-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "eks.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "eks_cluster_policy" {
  role       = aws_iam_role.eks_cluster.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
}

# ========== Outputs ==========

output "eks_cluster_endpoint" {
  value = aws_eks_cluster.main.endpoint
}

output "rds_endpoint" {
  value = aws_db_instance.main.endpoint
}

output "redis_endpoint" {
  value = aws_elasticache_cluster.redis.cache_nodes[0].address
}
