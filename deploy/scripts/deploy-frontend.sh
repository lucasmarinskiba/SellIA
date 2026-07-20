#!/usr/bin/env bash
# Deploy frontend to Vercel. Requires: vercel CLI, .env.production.
set -euo pipefail

cd "$(dirname "$0")/../../frontend"

command -v vercel >/dev/null 2>&1 || { echo "✗ vercel CLI missing · npm i -g vercel"; exit 1; }

echo "→ Type-check"
npx tsc --noEmit --skipLibCheck

echo "→ Lint"
npm run lint || true

echo "→ Build local sanity"
npm run build

echo "→ Deploy production"
vercel --prod --yes

echo "✓ Frontend deployed"
