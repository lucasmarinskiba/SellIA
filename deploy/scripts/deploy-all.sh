#!/usr/bin/env bash
# Full production deploy · DNS → backend → frontend.
set -euo pipefail

cd "$(dirname "$0")"

echo "════════════════════════════════════════"
echo "  SellIA · production deploy"
echo "════════════════════════════════════════"

./deploy-dns.sh
./deploy-backend.sh
./deploy-frontend.sh

echo ""
echo "✓ All deployed. Verify:"
echo "  · https://sellia.app"
echo "  · https://app.sellia.app"
echo "  · https://api.sellia.app/healthz"
