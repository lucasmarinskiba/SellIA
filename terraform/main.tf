# SellIA Production Infrastructure as Code
# Deploys complete production infrastructure: DB, Redis, monitoring, etc.
#
# Usage:
#   terraform init
#   terraform plan
#   terraform apply

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "sellia-terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "sellia-terraform-locks"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "SellIA"
      Environment = var.environment
      ManagedBy   = "Terraform"
      CreatedAt   = timestamp()
    }
  }
}

###############################################################################
# VPC & Networking
###############################################################################

resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "sellia-vpc"
  }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "sellia-igw"
  }
}

# Public subnets for NAT/Bastion
resource "aws_subnet" "public" {
  count                   = 2
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_cidrs[count.index]
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name = "sellia-public-${count.index + 1}"
  }
}

# Private subnets for RDS/Redis/Fargate
resource "aws_subnet" "private" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.private_subnet_cidrs[count.index]
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "sellia-private-${count.index + 1}"
  }
}

# Route tables
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block      = "0.0.0.0/0"
    gateway_id      = aws_internet_gateway.main.id
  }

  tags = {
    Name = "sellia-public-rt"
  }
}

resource "aws_route_table_association" "public" {
  count          = 2
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_eip" "nat" {
  domain = "vpc"
  tags = {
    Name = "sellia-nat-eip"
  }
  depends_on = [aws_internet_gateway.main]
}

resource "aws_nat_gateway" "main" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public[0].id

  tags = {
    Name = "sellia-nat-gw"
  }
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main.id
  }

  tags = {
    Name = "sellia-private-rt"
  }
}

resource "aws_route_table_association" "private" {
  count          = 2
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private.id
}

###############################################################################
# Security Groups
###############################################################################

resource "aws_security_group" "alb" {
  name_prefix = "sellia-alb-"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "sellia-alb-sg"
  }
}

resource "aws_security_group" "backend" {
  name_prefix = "sellia-backend-"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "sellia-backend-sg"
  }
}

resource "aws_security_group" "rds" {
  name_prefix = "sellia-rds-"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.backend.id]
  }

  tags = {
    Name = "sellia-rds-sg"
  }
}

resource "aws_security_group" "redis" {
  name_prefix = "sellia-redis-"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.backend.id]
  }

  tags = {
    Name = "sellia-redis-sg"
  }
}

###############################################################################
# RDS PostgreSQL
###############################################################################

resource "aws_db_subnet_group" "main" {
  name_prefix = "sellia-"
  subnet_ids  = aws_subnet.private[*].id

  tags = {
    Name = "sellia-db-subnet-group"
  }
}

resource "aws_rds_cluster_parameter_group" "main" {
  name_prefix = "sellia-"
  family      = "aurora-postgresql15"

  parameter {
    name  = "log_statement"
    value = "ddl"
  }

  parameter {
    name  = "log_duration"
    value = "1"
  }

  parameter {
    name  = "log_min_duration_statement"
    value = "1000"
  }

  tags = {
    Name = "sellia-db-cluster-params"
  }
}

resource "aws_rds_cluster" "main" {
  cluster_identifier_prefix        = "sellia-"
  engine                           = "aurora-postgresql"
  engine_version                   = "15.3"
  database_name                    = var.db_name
  master_username                  = var.db_username
  master_password                  = var.db_password
  db_subnet_group_name             = aws_db_subnet_group.main.name
  vpc_security_group_ids           = [aws_security_group.rds.id]
  db_cluster_parameter_group_name  = aws_rds_cluster_parameter_group.main.name
  backup_retention_period          = 30
  copy_tags_to_snapshot            = true
  enabled_cloudwatch_logs_exports  = ["postgresql"]
  storage_encrypted                = true
  kms_key_id                       = aws_kms_key.rds.arn
  skip_final_snapshot              = false
  final_snapshot_identifier_prefix = "sellia-final-"

  tags = {
    Name = "sellia-db-cluster"
  }
}

resource "aws_rds_cluster_instance" "main" {
  count              = var.db_instance_count
  identifier_prefix  = "sellia-db-"
  cluster_identifier = aws_rds_cluster.main.id
  instance_class     = var.db_instance_class
  engine             = aws_rds_cluster.main.engine
  engine_version     = aws_rds_cluster.main.engine_version

  performance_insights_enabled    = true
  monitoring_interval             = 60
  monitoring_role_arn             = aws_iam_role.rds_monitoring.arn
  auto_minor_version_upgrade      = true

  tags = {
    Name = "sellia-db-instance-${count.index + 1}"
  }
}

###############################################################################
# ElastiCache Redis
###############################################################################

resource "aws_elasticache_subnet_group" "main" {
  name_prefix = "sellia-"
  subnet_ids  = aws_subnet.private[*].id

  tags = {
    Name = "sellia-redis-subnet-group"
  }
}

resource "aws_elasticache_cluster" "main" {
  cluster_id_prefix      = "sellia-"
  engine                 = "redis"
  engine_version         = "7.0"
  node_type              = var.redis_node_type
  num_cache_nodes        = var.redis_node_count
  parameter_group_name   = "default.redis7"
  port                   = 6379
  subnet_group_name      = aws_elasticache_subnet_group.main.name
  security_group_ids     = [aws_security_group.redis.id]
  automatic_failover_enabled = true
  multi_az_enabled       = var.redis_node_count > 1
  at_rest_encryption_enabled = true
  auth_token             = random_password.redis_auth_token.result
  transit_encryption_enabled = true
  notification_topic_arn = aws_sns_topic.elasticache_notifications.arn

  tags = {
    Name = "sellia-redis"
  }

  depends_on = [aws_elasticache_subnet_group.main]
}

###############################################################################
# IAM Roles
###############################################################################

resource "aws_iam_role" "rds_monitoring" {
  name_prefix = "sellia-rds-monitoring-"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "monitoring.rds.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "rds_monitoring" {
  role       = aws_iam_role.rds_monitoring.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}

###############################################################################
# KMS Encryption
###############################################################################

resource "aws_kms_key" "rds" {
  description             = "KMS key for RDS encryption"
  deletion_window_in_days = 10
  enable_key_rotation     = true

  tags = {
    Name = "sellia-rds-key"
  }
}

resource "aws_kms_alias" "rds" {
  name          = "alias/sellia-rds"
  target_key_id = aws_kms_key.rds.key_id
}

###############################################################################
# SNS Topics (for notifications)
###############################################################################

resource "aws_sns_topic" "elasticache_notifications" {
  name_prefix = "sellia-elasticache-"

  tags = {
    Name = "sellia-elasticache-notifications"
  }
}

resource "aws_sns_topic_subscription" "elasticache_notifications" {
  topic_arn = aws_sns_topic.elasticache_notifications.arn
  protocol  = "email"
  endpoint  = var.ops_email
}

###############################################################################
# Outputs
###############################################################################

output "rds_endpoint" {
  description = "RDS cluster endpoint"
  value       = aws_rds_cluster.main.endpoint
  sensitive   = false
}

output "rds_reader_endpoint" {
  description = "RDS cluster reader endpoint"
  value       = aws_rds_cluster.main.reader_endpoint
  sensitive   = false
}

output "redis_endpoint" {
  description = "Redis cluster endpoint"
  value       = aws_elasticache_cluster.main.cache_nodes[0].address
  sensitive   = false
}

output "redis_port" {
  description = "Redis port"
  value       = aws_elasticache_cluster.main.port
  sensitive   = false
}

output "database_url" {
  description = "PostgreSQL connection string"
  value       = "postgresql://${var.db_username}:PASSWORD@${aws_rds_cluster.main.endpoint}:5432/${var.db_name}"
  sensitive   = true
}

output "redis_url" {
  description = "Redis connection string"
  value       = "redis://:AUTH_TOKEN@${aws_elasticache_cluster.main.cache_nodes[0].address}:${aws_elasticache_cluster.main.port}/0"
  sensitive   = true
}
