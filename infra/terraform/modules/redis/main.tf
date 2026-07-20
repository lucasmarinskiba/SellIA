resource "aws_elasticache_subnet_group" "main" {
  name       = "${var.environment}-sellia-redis"
  subnet_ids = var.subnet_ids
}

resource "aws_security_group" "redis" {
  name_prefix = "${var.environment}-redis-"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = var.allowed_cidr_blocks
  }

  tags = {
    Name = "${var.environment}-redis"
  }
}

resource "aws_elasticache_replication_group" "main" {
  replication_group_id = "${var.environment}-sellia-redis"
  description          = "Redis cluster for SellIA"

  engine               = "redis"
  engine_version       = "7.1"
  node_type            = var.node_type
  num_cache_clusters   = var.environment == "production" ? 2 : 1
  automatic_failover_enabled = var.environment == "production"

  subnet_group_name  = aws_elasticache_subnet_group.main.name
  security_group_ids = [aws_security_group.redis.id]

  at_rest_encryption_enabled = true
  transit_encryption_enabled = true

  snapshot_retention_limit = 7
  snapshot_window         = "05:00-06:00"

  tags = {
    Name = "${var.environment}-sellia-redis"
  }
}
