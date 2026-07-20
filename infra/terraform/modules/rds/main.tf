resource "aws_db_subnet_group" "main" {
  name       = "${var.environment}-sellia-db"
  subnet_ids = var.subnet_ids

  tags = {
    Name = "${var.environment}-sellia-db"
  }
}

resource "aws_security_group" "rds" {
  name_prefix = "${var.environment}-rds-"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = var.allowed_cidr_blocks
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.environment}-rds"
  }
}

resource "aws_db_instance" "main" {
  identifier = "${var.environment}-sellia-postgres"

  engine               = "postgres"
  engine_version       = "16.1"
  instance_class       = var.instance_class
  allocated_storage    = 20
  max_allocated_storage = 100
  storage_type         = "gp3"
  storage_encrypted    = true

  db_name  = var.db_name
  username = var.db_username
  password = var.db_password

  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name

  multi_az               = var.environment == "production"
  publicly_accessible    = false
  skip_final_snapshot    = var.environment != "production"
  deletion_protection    = var.environment == "production"

  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "Mon:04:00-Mon:05:00"

  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]

  tags = {
    Name = "${var.environment}-sellia-postgres"
  }
}

resource "aws_cloudwatch_log_group" "rds" {
  name              = "/aws/rds/instance/${aws_db_instance.main.identifier}/postgresql"
  retention_in_days = 7
}
