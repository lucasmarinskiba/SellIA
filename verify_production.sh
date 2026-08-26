#!/bin/bash
# Production verification script — run after Railway deployment is live

set -e

# Try these URLs in order
URLS=(
  "https://sellia-api.railway.app/api/health"
  "https://sellbot-api.railway.app/api/health"
  "https://backend.railway.app/api/health"
  "https://api.railway.app/health"
)

echo "Checking production deployment..."
echo ""

for url in "${URLS[@]}"; do
  echo "Trying: $url"
  response=$(curl -s -m 5 "$url" 2>&1 || true)
  if echo "$response" | grep -q "ok\|200"; then
    echo "✅ FOUND: $url"
    echo "Response: $response"
    echo ""
    echo "Next: Run e2e tests against this URL"
    echo "See: memory/phase_29_e2e_test_plan.md"
    exit 0
  else
    echo "  Not responding"
  fi
done

echo ""
echo "No production URL responding yet."
echo "Check Railway dashboard: https://railway.app/"
echo "Look for: auto-deploy completed"
