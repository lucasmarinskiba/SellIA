#!/bin/bash
set -e

echo "=== SellIA Backend Deploy to Fly.io ==="

cd backend

# 1. Login
echo "1. Logging in to Fly.io..."
flyctl auth login

# 2. Create app
echo "2. Creating Fly app..."
flyctl launch --no-deploy || true  # Si existe, ignora error

# 3. Create PostgreSQL
echo "3. Creating PostgreSQL database..."
flyctl postgres create --name selliadb --region gru || true

# 4. Attach database
echo "4. Attaching database to app..."
flyctl postgres attach selliadb || true

# 5. Create Redis
echo "5. Creating Redis (via Upstash)..."
flyctl redis create --region gru || true

# 6. Set secrets
echo "6. Setting environment variables..."
flyctl secrets set \
  ENVIRONMENT=production \
  FRONTEND_URL=https://sellia-brain.vercel.app \
  SENDGRID_API_KEY=${SENDGRID_API_KEY:-"your-key-here"} \
  ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-"your-key-here"}

# 7. Deploy
echo "7. Deploying..."
flyctl deploy --remote-only

# 8. Health check
echo "8. Checking health..."
sleep 10
flyctl status

echo ""
echo "✅ Deployment complete!"
echo "Backend URL: https://selliaai.fly.dev"
echo ""
echo "Next steps:"
echo "1. Update frontend .env.production:"
echo "   NEXT_PUBLIC_API_URL=https://api.selliaai.fly.dev"
echo "2. Deploy frontend to Vercel"
echo "3. Add custom domain if needed:"
echo "   flyctl certs add api.sellia.app"
