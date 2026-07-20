locals {
  cluster_name = var.cluster_name
}

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"

  cluster_name    = local.cluster_name
  cluster_version = var.cluster_version

  vpc_id     = var.vpc_id
  subnet_ids = var.subnet_ids

  # Fargate profiles para workloads serverless
  fargate_profiles = {
    default = {
      name = "default"
      selectors = [
        { namespace = "sellia" }
      ]
    }
  }

  # Managed node groups para workloads con estado
  eks_managed_node_groups = {
    for name, config in var.node_groups : name => {
      name           = name
      desired_size   = config.desired_size
      min_size       = config.min_size
      max_size       = config.max_size
      instance_types = config.instance_types
      capacity_type  = "ON_DEMAND"

      iam_role_additional_policies = {
        CloudWatchAgentServerPolicy = "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
        AmazonSSMManagedInstanceCore = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
      }
    }
  }

  # Habilitar IRSA (IAM Roles for Service Accounts)
  enable_irsa = true

  # Encriptación del cluster
  cluster_encryption_config = {
    provider_key_arn = aws_kms_key.eks.arn
    resources        = ["secrets"]
  }

  # CloudWatch logging
  cluster_enabled_log_types = ["api", "audit", "authenticator", "controllerManager", "scheduler"]
}

resource "aws_kms_key" "eks" {
  description             = "EKS Secret Encryption Key"
  deletion_window_in_days = 7
  enable_key_rotation     = true
}

resource "aws_kms_alias" "eks" {
  name          = "alias/${var.cluster_name}-eks"
  target_key_id = aws_kms_key.eks.key_id
}
