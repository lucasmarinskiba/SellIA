output "logs_bucket_name" {
  value = aws_s3_bucket.logs.bucket
}

output "assets_bucket_name" {
  value = aws_s3_bucket.assets.bucket
}

output "assets_bucket_domain_name" {
  value = aws_s3_bucket.assets.bucket_regional_domain_name
}
