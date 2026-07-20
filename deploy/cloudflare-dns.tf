# Cloudflare DNS · Terraform template for sellia.app
# Usage:
#   export CLOUDFLARE_API_TOKEN=...
#   terraform init && terraform plan && terraform apply

terraform {
  required_version = ">= 1.7"
  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 4.40"
    }
  }
}

variable "zone_id" {
  type        = string
  description = "Cloudflare zone id for sellia.app"
}

variable "vercel_cname" {
  type        = string
  default     = "cname.vercel-dns.com"
  description = "Vercel CNAME target"
}

variable "api_origin" {
  type        = string
  description = "Backend host (Fly/Railway/Hetzner) · e.g. sellia-api.fly.dev"
}

provider "cloudflare" {}

# Root + www → frontend (Vercel)
resource "cloudflare_record" "root" {
  zone_id = var.zone_id
  name    = "@"
  type    = "A"
  value   = "76.76.21.21"  # Vercel anycast
  proxied = true
  ttl     = 1
}

resource "cloudflare_record" "www" {
  zone_id = var.zone_id
  name    = "www"
  type    = "CNAME"
  value   = var.vercel_cname
  proxied = true
  ttl     = 1
}

resource "cloudflare_record" "app" {
  zone_id = var.zone_id
  name    = "app"
  type    = "CNAME"
  value   = var.vercel_cname
  proxied = true
  ttl     = 1
}

# Wildcard for tenant subdomains: *.sellia.app
resource "cloudflare_record" "wildcard" {
  zone_id = var.zone_id
  name    = "*"
  type    = "CNAME"
  value   = var.vercel_cname
  proxied = true
  ttl     = 1
}

# API subdomain → backend
resource "cloudflare_record" "api" {
  zone_id = var.zone_id
  name    = "api"
  type    = "CNAME"
  value   = var.api_origin
  proxied = true
  ttl     = 1
}

# SPF · DKIM · DMARC (transactional + outbound · adjust if using Resend/Postmark)
resource "cloudflare_record" "spf" {
  zone_id = var.zone_id
  name    = "@"
  type    = "TXT"
  value   = "v=spf1 include:_spf.resend.com include:_spf.mx.cloudflare.net -all"
  ttl     = 3600
}

resource "cloudflare_record" "dmarc" {
  zone_id = var.zone_id
  name    = "_dmarc"
  type    = "TXT"
  value   = "v=DMARC1; p=quarantine; rua=mailto:dmarc@sellia.app; sp=reject; adkim=s; aspf=s"
  ttl     = 3600
}

# MX records (using Resend or Cloudflare Email Routing)
resource "cloudflare_record" "mx_route1" {
  zone_id  = var.zone_id
  name     = "@"
  type     = "MX"
  value    = "route1.mx.cloudflare.net"
  priority = 26
}

resource "cloudflare_record" "mx_route2" {
  zone_id  = var.zone_id
  name     = "@"
  type     = "MX"
  value    = "route2.mx.cloudflare.net"
  priority = 18
}

resource "cloudflare_record" "mx_route3" {
  zone_id  = var.zone_id
  name     = "@"
  type     = "MX"
  value    = "route3.mx.cloudflare.net"
  priority = 90
}

# Cloudflare Page Rules · force HTTPS · cache static
resource "cloudflare_page_rule" "force_https" {
  zone_id  = var.zone_id
  target   = "*sellia.app/*"
  priority = 1
  status   = "active"

  actions {
    always_use_https = true
  }
}
