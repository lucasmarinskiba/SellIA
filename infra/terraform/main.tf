# ============================================================
#  SellIA Infrastructure as Code — Terraform (AWS)
#  Despliega toda la infraestructura necesaria para SellIA
#  en AWS: VPC, EKS, RDS, ElastiCache, ALB, S3, CloudFront
# ============================================================

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.11"
    }
  }

  backend "s3" {
    bucket         = "sellia-terraform-state"
    key            = "infrastructure/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "sellia-terraform-locks"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "sellia"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

# VPC y Networking
module "vpc" {
  source = "./modules/vpc"

  environment = var.environment
  vpc_cidr    = var.vpc_cidr
  azs         = var.availability_zones
}

# IAM Roles
module "iam" {
  source = "./modules/iam"

  environment = var.environment
  cluster_name = var.cluster_name
}

# EKS Cluster
module "eks" {
  source = "./modules/eks"

  environment    = var.environment
  cluster_name   = var.cluster_name
  cluster_version = var.kubernetes_version
  vpc_id         = module.vpc.vpc_id
  subnet_ids     = module.vpc.private_subnet_ids
  node_groups    = var.eks_node_groups
}

# RDS PostgreSQL
module "rds" {
  source = "./modules/rds"

  environment         = var.environment
  vpc_id              = module.vpc.vpc_id
  subnet_ids          = module.vpc.database_subnet_ids
  allowed_cidr_blocks = [module.vpc.vpc_cidr_block]
  instance_class      = var.rds_instance_class
  db_name             = var.db_name
  db_username         = var.db_username
  db_password         = var.db_password
}

# ElastiCache Redis
module "redis" {
  source = "./modules/redis"

  environment         = var.environment
  vpc_id              = module.vpc.vpc_id
  subnet_ids          = module.vpc.elasticache_subnet_ids
  allowed_cidr_blocks = [module.vpc.vpc_cidr_block]
  node_type           = var.redis_node_type
}

# Application Load Balancer
module "alb" {
  source = "./modules/alb"

  environment = var.environment
  vpc_id      = module.vpc.vpc_id
  subnet_ids  = module.vpc.public_subnet_ids
  certificate_arn = var.acm_certificate_arn
}

# S3 Bucket para logs y assets
module "s3" {
  source = "./modules/s3"

  environment   = var.environment
  bucket_prefix = var.s3_bucket_prefix
}

# CloudFront CDN
module "cloudfront" {
  source = "./modules/cloudfront"

  environment         = var.environment
  alb_dns_name        = module.alb.dns_name
  s3_bucket_domain_name = module.s3.assets_bucket_domain_name
  certificate_arn     = var.acm_certificate_arn_cloudfront
}

# Sidecar ECR Repository
module "sidecar" {
  source = "./modules/sidecar"

  project_name = var.project_name
  environment  = var.environment
}

# Envoy Edge Proxy (placeholder para WAF/ALB dedicado)
module "envoy" {
  source = "./modules/envoy"

  project_name = var.project_name
  environment  = var.environment
}

data "aws_eks_cluster_auth" "cluster" {
  name = module.eks.cluster_name
}

# Configuración de proveedores K8s/Helm
provider "kubernetes" {
  host                   = module.eks.cluster_endpoint
  cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority)
  token                  = data.aws_eks_cluster_auth.cluster.token
}

provider "helm" {
  kubernetes {
    host                   = module.eks.cluster_endpoint
    cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority)
    token                  = data.aws_eks_cluster_auth.cluster.token
  }
}
