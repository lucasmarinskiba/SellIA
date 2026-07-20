#!/usr/bin/env bash
# Deploy backend to Fly.io. Requires: flyctl, .env.production.
set -euo pipefail

cd "$(dirname "$0")/../../backend-mvp"

# Sanity checks
command -v fly >/dev/null 2>&1 || { echo "✗ flyctl missing · curl -L https://fly.io/install.sh | sh"; exit 1; }
[ -f .env.production ] || { echo "✗ backend-mvp/.env.production missing"; exit 1; }

echo "→ Set fly secrets from .env.production"
# Read env file, strip comments/blanks, push each VAR=value to fly secrets.
while IFS='=' read -r key val; do
  [[ "$key" =~ ^[[:space:]]*# || -z "$key" ]] && continue
  val="${val%\"}"; val="${val#\"}"  # strip wrapping quotes
  fly secrets set "$key=$val" --stage 1>/dev/null
done < <(grep -E '^[A-Z_]+=' .env.production)

fly secrets deploy

echo "→ Deploy api"
fly deploy --strategy rolling --wait-timeout 300

echo "→ Run migrations explicitly (release_command handles it but be safe)"
fly ssh console -C "alembic upgrade head" || true

echo "→ Scale workers"
fly scale count 2 --process-group worker || true

echo "✓ Backend deployed · https://sellia-api.fly.dev"
fly status
