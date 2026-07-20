#!/usr/bin/env bash
# Apply DNS via Terraform.
set -euo pipefail

cd "$(dirname "$0")/../terraform"

command -v terraform >/dev/null 2>&1 || { echo "✗ terraform missing"; exit 1; }
[ -f terraform.tfvars ] || { echo "✗ terraform.tfvars missing · copy from .example"; exit 1; }

terraform init
terraform plan -out=tfplan
echo "→ Review plan above. Press enter to apply or Ctrl+C to abort."
read -r
terraform apply tfplan
rm -f tfplan
echo "✓ DNS applied"
