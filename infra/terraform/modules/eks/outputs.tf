output "cluster_endpoint" {
  value = module.eks.cluster_endpoint
}

output "cluster_certificate_authority" {
  value = module.eks.cluster_certificate_authority_data
}

output "cluster_name" {
  value = module.eks.cluster_name
}

output "cluster_oidc_issuer_url" {
  value = module.eks.cluster_oidc_issuer_url
}
