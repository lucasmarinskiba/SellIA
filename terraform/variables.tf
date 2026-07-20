# Terraform Variables for SellIA Production Infrastructure

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
  validation {
    condition     = contains(["production", "staging", "development"], var.environment)
    error_message = "Environment must be one of: production, staging, development"
  }
}

# VPC Configuration
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.10.0/24", "10.0.11.0/24"]
}

# Database Configuration
variable "db_name" {
  description = "Name of the initial database"
  type        = string
  default     = "selliadb"
  sensitive   = true
}

variable "db_username" {
  description = "Master username for database"
  type        = string
  default     = "selliauser"
  sensitive   = true
}

variable "db_password" {
  description = "Master password for database (should be generated and stored securely)"
  type        = string
  sensitive   = true
  validation {
    condition     = length(var.db_password) >= 16
    error_message = "Database password must be at least 16 characters"
  }
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t4g.large"
}

variable "db_instance_count" {
  description = "Number of RDS instances in cluster"
  type        = number
  default     = 2
  validation {
    condition     = var.db_instance_count >= 1 && var.db_instance_count <= 5
    error_message = "Instance count must be between 1 and 5"
  }
}

# Redis Configuration
variable "redis_node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.t4g.medium"
}

variable "redis_node_count" {
  description = "Number of Redis nodes"
  type        = number
  default     = 2
  validation {
    condition     = var.redis_node_count >= 1 && var.redis_node_count <= 5
    error_message = "Node count must be between 1 and 5"
  }
}

# Monitoring & Alerts
variable "ops_email" {
  description = "Email for operational alerts"
  type        = string
}

# Tags
variable "tags" {
  description = "Additional tags to apply to resources"
  type        = map(string)
  default = {
    Project = "SellIA"
    Owner   = "Engineering"
  }
}
