output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "eks_cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = module.eks.cluster_endpoint
}

output "eks_cluster_name" {
  description = "EKS cluster name"
  value       = module.eks.cluster_name
}

output "rds_endpoint" {
  description = "RDS endpoint"
  value       = module.rds.endpoint
  sensitive   = true
}

output "redis_endpoint" {
  description = "Redis endpoint"
  value       = module.redis.endpoint
  sensitive   = true
}

output "alb_dns_name" {
  description = "ALB DNS name"
  value       = module.alb.dns_name
}

output "cloudfront_domain_name" {
  description = "CloudFront domain name"
  value       = module.cloudfront.domain_name
}

output "s3_logs_bucket" {
  description = "S3 logs bucket name"
  value       = module.s3.logs_bucket_name
}

output "s3_assets_bucket" {
  description = "S3 assets bucket name"
  value       = module.s3.assets_bucket_name
}
