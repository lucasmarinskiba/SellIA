locals {
  name = "${var.environment}-sellia"
}

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = local.name
  cidr = var.vpc_cidr

  azs             = var.azs
  private_subnets = [for i, az in var.azs : cidrsubnet(var.vpc_cidr, 4, i)]
  public_subnets  = [for i, az in var.azs : cidrsubnet(var.vpc_cidr, 4, i + length(var.azs))]
  database_subnets = [for i, az in var.azs : cidrsubnet(var.vpc_cidr, 4, i + 2 * length(var.azs))]
  elasticache_subnets = [for i, az in var.azs : cidrsubnet(var.vpc_cidr, 4, i + 3 * length(var.azs))]

  enable_nat_gateway     = true
  single_nat_gateway     = var.environment != "production"
  enable_dns_hostnames   = true
  enable_dns_support     = true

  # Tags para que el CSI driver de EBS encuentre las subnets
  public_subnet_tags = {
    "kubernetes.io/role/elb" = "1"
    "kubernetes.io/cluster/${local.name}" = "shared"
  }
  private_subnet_tags = {
    "kubernetes.io/role/internal-elb" = "1"
    "kubernetes.io/cluster/${local.name}" = "shared"
  }
}
