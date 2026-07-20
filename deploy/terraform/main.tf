terraform {
  required_version = ">= 1.5"

  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 4.40"
    }
  }

  backend "s3" {
    # Use Cloudflare R2 as S3-compatible backend (or local for dev)
    # bucket = "sellia-tfstate"
    # key    = "terraform.tfstate"
    # endpoint = "https://xxx.r2.cloudflarestorage.com"
  }
}

provider "cloudflare" {
  api_token = var.cloudflare_api_token
}

variable "cloudflare_api_token" { type = string; sensitive = true }
variable "zone_id"             { type = string }
variable "domain"              { type = string; default = "sellia.app" }
variable "vercel_dns_target"   { type = string; default = "cname.vercel-dns.com" }
variable "api_dns_target"      { type = string; default = "sellia-api.fly.dev" }

# Root domain → Vercel
resource "cloudflare_record" "root" {
  zone_id = var.zone_id
  name    = "@"
  type    = "CNAME"
  content = var.vercel_dns_target
  proxied = true
  ttl     = 1
  comment = "Vercel root · proxied"
}

# www → root (redirect via page rules)
resource "cloudflare_record" "www" {
  zone_id = var.zone_id
  name    = "www"
  type    = "CNAME"
  content = var.domain
  proxied = true
  ttl     = 1
}

# app subdomain (Vercel)
resource "cloudflare_record" "app" {
  zone_id = var.zone_id
  name    = "app"
  type    = "CNAME"
  content = var.vercel_dns_target
  proxied = true
  ttl     = 1
}

# api subdomain (Fly.io · proxied OFF · let Fly handle TLS)
resource "cloudflare_record" "api" {
  zone_id = var.zone_id
  name    = "api"
  type    = "CNAME"
  content = var.api_dns_target
  proxied = false
  ttl     = 300
}

# Email · ImprovMX / Forwarding · placeholders
resource "cloudflare_record" "mx_primary" {
  zone_id  = var.zone_id
  name     = "@"
  type     = "MX"
  content  = "mx1.improvmx.com"
  priority = 10
  ttl      = 3600
}

resource "cloudflare_record" "mx_secondary" {
  zone_id  = var.zone_id
  name     = "@"
  type     = "MX"
  content  = "mx2.improvmx.com"
  priority = 20
  ttl      = 3600
}

# SPF
resource "cloudflare_record" "spf" {
  zone_id = var.zone_id
  name    = "@"
  type    = "TXT"
  content = "v=spf1 include:_spf.improvmx.com include:_spf.resend.com -all"
  ttl     = 3600
}

# DMARC
resource "cloudflare_record" "dmarc" {
  zone_id = var.zone_id
  name    = "_dmarc"
  type    = "TXT"
  content = "v=DMARC1; p=quarantine; rua=mailto:dmarc@${var.domain}; fo=1"
  ttl     = 3600
}

# Cloudflare Worker for edge transforms (optional)
# Define separately in workers/ directory.

# Outputs
output "nameservers_hint" {
  value = "Apuntar registrar a Cloudflare nameservers."
}
