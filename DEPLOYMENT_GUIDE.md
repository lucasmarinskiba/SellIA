# SellIA Production Deployment Guide

Complete step-by-step guide for deploying SellIA to production. From zero to live in ~45 minutes.

**Status:** ✅ Production Ready  
**Estimated Time:** 45 minutes  
**Difficulty:** Intermediate (experienced DevOps/Backend engineer)

---

## Quick Start (TL;DR)

```bash
# 1. Generate credentials
python3 scripts/generate-credentials.py

# 2. Validate environment
python3 scripts/validate-env.py

# 3. Deploy everything
./scripts/deploy-all.sh all

# 4. Run health checks
./scripts/health-check.sh 0  # single run

# 5. Run E2E tests
npm run test:e2e
```

---

## Prerequisites

### Required Tools
```bash
# Fly.io CLI
curl -L https://fly.io/install.sh | sh

# Vercel CLI
npm install -g vercel

# Node 20+
node --version  # Should be v20.x or higher

# Python 3.12+
python3 --version

# Docker
docker --version

# PostgreSQL client
psql --version
```

### Required Accounts
- ✅ Fly.io (backend hosting)
- ✅ Vercel (frontend hosting)
- ✅ Stripe (payments - LIVE mode)
- ✅ SendGrid (email)
- ✅ Sentry (error tracking)
- ✅ GitHub (CI/CD secrets)

### Credentials Needed
Before you start, gather these:
```
Database: PostgreSQL password
Redis: Redis password
Stripe: Live API key (sk_live_...), webhook secret
SendGrid: API key
Sentry: DSN
Vercel: API token
Fly.io: API token
```

---

## Step 1: Generate Credentials (5 min)

### 1.1 Run Credential Generator
```bash
python3 scripts/generate-credentials.py
```

**Output:**
```
DB_PASSWORD=x7kL9mP2qR8vN3bJ5cD1eF4gH6iK9oL2
REDIS_PASSWORD=a1B2c3D4e5F6g7H8i9J0k1L2m3N4o5P6
SECRET_KEY=q8w7e6r5t4y3u2i1o0p9a8s7d6f5g4h3j2k1l0m9n8b7v6c5x4z3a2s1d0f9g8h7
JWT_SECRET=[base64-encoded-secret]
API_KEY=[random-hex-key]
```

### 1.2 Manual Credentials
You'll still need to get these manually:

**Stripe:**
1. Go to https://dashboard.stripe.com/apikeys
2. Switch to LIVE mode (top toggle)
3. Copy "Secret Key" (starts with `sk_live_`)
4. Go to https://dashboard.stripe.com/webhooks
5. Copy webhook secret

**SendGrid:**
1. Go to https://app.sendgrid.com/settings/api_keys
2. Create "Mail Send" key
3. Copy the key

**Sentry:**
1. Go to https://sentry.io
2. Create project
3. Copy DSN

---

## Step 2: Create .env.production (10 min)

### 2.1 Copy Template
```bash
cp .env.production .env.production.local
```

### 2.2 Fill In Values
```bash
# Database
DATABASE_URL=postgresql://selliauser:PASSWORD@db-host:5432/selliadb
REDIS_URL=redis://:PASSWORD@redis-host:6379/0

# Secrets (from credential generator)
SECRET_KEY=xxx
JWT_SECRET=xxx

# Domain
FRONTEND_URL=https://selldia.app
BACKEND_URL=https://api.sellia.app

# Payment (from Stripe dashboard)
STRIPE_API_KEY=sk_live_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
STRIPE_PUBLISHABLE_KEY=pk_live_xxx

# Email (from SendGrid)
SENDGRID_API_KEY=SG.xxx

# Monitoring (from Sentry)
SENTRY_DSN=https://xxx@xxx.ingest.sentry.io/xxx

# Security
SECURE_SSL_REDIRECT=true
SESSION_COOKIE_SECURE=true
DEBUG=false
```

### 2.3 Validate Configuration
```bash
python3 scripts/validate-env.py

# Output should show:
# ✅ ALL CHECKS PASSED
# Total required variables: 45
```

---

## Step 3: Database Setup (10 min)

### 3.1 Choose Hosting Option

#### Option A: Railway (Recommended - Easiest)
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Create PostgreSQL
cd backend-mvp
railway add
# Select "PostgreSQL"

# Get connection string
railway open
# Copy DATABASE_URL from Variables tab
```

#### Option B: AWS RDS
```bash
# Create RDS instance
aws rds create-db-instance \
  --db-instance-identifier sellia-db \
  --engine postgres \
  --db-instance-class db.t3.micro \
  --allocated-storage 100

# Wait for creation (10-15 min)
aws rds describe-db-instances --db-instance-identifier sellia-db

# Get endpoint
ENDPOINT=$(aws rds describe-db-instances \
  --db-instance-identifier sellia-db \
  --query 'DBInstances[0].Endpoint.Address' --output text)

# DATABASE_URL=postgresql://selliauser:PASSWORD@$ENDPOINT:5432/selliadb
```

#### Option C: Fly.io Postgres
```bash
fly postgres create -a sellia-api --name postgres
# Connection auto-added to secrets
```

### 3.2 Test Connection
```bash
psql $DATABASE_URL -c "SELECT version();"
# Should output: PostgreSQL 15.x (Debian ...)
```

### 3.3 Run Migrations
```bash
cd backend-mvp
alembic upgrade head

# Output:
# INFO  [alembic.runtime.migration] Running upgrade 001_initial -> 002_add_users
# ...
# INFO  [alembic.runtime.migration] Running upgrade 00N_latest -> head
```

### 3.4 Verify Database
```bash
psql $DATABASE_URL << 'EOF'
SELECT COUNT(*) FROM pg_tables WHERE schemaname = 'public';
SELECT * FROM alembic_version;
EOF
```

---

## Step 4: Setup Infrastructure (10 min)

### 4.1 Fly.io Backend Setup
```bash
# Authenticate
fly auth login

# Create app (if not exists)
cd backend-mvp
fly launch --no-deploy --name sellia-api --region gru

# Set all secrets
fly secrets set \
  DATABASE_URL='postgresql://...' \
  REDIS_URL='redis://...' \
  SECRET_KEY='...' \
  STRIPE_API_KEY='sk_live_...' \
  SENDGRID_API_KEY='SG...' \
  SENTRY_DSN='https://...'

# Verify
fly secrets list
```

### 4.2 Vercel Frontend Setup
```bash
# Authenticate
vercel login

# Link project
cd frontend
vercel link

# Set environment variables
vercel env add NEXT_PUBLIC_API_URL production
# Enter: https://api.sellia.app

vercel env add NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY production
# Enter: pk_live_xxx
```

### 4.3 GitHub Secrets
```bash
# Go to: Settings → Secrets and variables → Actions

# Add these secrets:
FLY_API_TOKEN          = [from fly auth token]
VERCEL_TOKEN           = [from vercel profile]
VERCEL_ORG_ID          = [from vercel dashboard]
VERCEL_PROJECT_ID      = [from vercel dashboard]
SLACK_DEPLOY_WEBHOOK   = [optional, for notifications]
```

---

## Step 5: Deploy Backend (5 min)

### 5.1 Manual Deploy
```bash
cd backend-mvp

# Build Docker image (test locally)
docker build -t sellia-backend .

# Deploy to Fly.io
fly deploy --remote-only

# Watch logs
fly logs -a sellia-api

# Check status
fly status
```

### 5.2 Verify Backend
```bash
# Health check
curl https://api.sellia.app/healthz
# Expected: {"status": "ok", "version": "1.0.0"}

# API test
curl https://api.sellia.app/api/v1/status
# Expected: {"service": "SellIA Backend", "alive": true}

# Latency test
time curl -s https://api.sellia.app/api/v1/status > /dev/null
# Should be < 200ms
```

### 5.3 View Logs
```bash
# Recent errors
fly logs -a sellia-api | grep -i error

# Database migrations
fly logs -a sellia-api | grep alembic

# Webhook processing
fly logs -a sellia-api | grep webhook
```

---

## Step 6: Deploy Frontend (3 min)

### 6.1 Build Locally
```bash
cd frontend

# Type check
npx tsc --noEmit --skipLibCheck

# Build
npm run build

# Verify build output
ls -la .next
```

### 6.2 Deploy to Vercel
```bash
# Deploy to production
vercel --prod --yes --token $VERCEL_TOKEN

# Output:
# ✅ Production deployment ready [selldia.vercel.app]
```

### 6.3 Verify Frontend
```bash
# Test homepage
curl https://selldia.app

# Check performance
curl https://selldia.app -w "\nTime: %{time_total}s\n"
# Should be < 3 seconds

# Verify API connectivity
curl https://selldia.app/api/health
```

---

## Step 7: Configure Payment (5 min)

### 7.1 Add Webhook to Stripe
```bash
# Go to: https://dashboard.stripe.com/webhooks
# Add endpoint:
#   URL: https://api.sellia.app/webhooks/stripe
#   Events: payment_intent.succeeded, payment_intent.payment_failed
# Copy webhook secret and add to environment
```

### 7.2 Test Payment
```bash
# Use Stripe test card (4242 4242 4242 4242)
# Then verify:

# 1. Check database
psql $DATABASE_URL -c "SELECT * FROM payments ORDER BY created_at DESC LIMIT 1;"

# 2. Check Sentry for webhook events
curl -s https://api.sentry.io/api/0/organizations/YOUR_ORG/issues/ \
  -H "Authorization: Bearer $SENTRY_TOKEN" | jq '.[] | .shortId'

# 3. Check email received
# (Check gmail/email for payment confirmation)
```

---

## Step 8: Run Tests (5 min)

### 8.1 E2E Tests
```bash
# Set test environment
export FRONTEND_URL=https://selldia.app
export BACKEND_URL=https://api.sellia.app

# Run tests
npm run test:e2e

# Expected output:
# ✓ Login flow (5s)
# ✓ Market detection (10s)
# ✓ Strategy selection (8s)
# ✓ Payment processing (15s)
# ✓ Dashboard updates (5s)
# All tests passed
```

### 8.2 Health Checks
```bash
# Run single health check
./scripts/health-check.sh 0

# Expected output:
# ✅ API health: HTTP 200 (145ms)
# ✅ Database: Connected
# ✅ Redis: Connected
# ✅ Frontend: HTTP 200
# ✅ Webhook endpoint: HTTP 405
# ✅ Email: SendGrid API connected
# ✅ SSL: Backend expires [date]
# ✅ Monitoring: Sentry configured
# All systems nominal
```

### 8.3 Performance Tests
```bash
# API latency
ab -n 100 -c 5 https://api.sellia.app/api/v1/status

# Expected:
# Requests per second: > 50
# Time per request: < 50ms

# Frontend performance
lighthouse https://selldia.app --output-path=report.html

# Expected scores:
# Performance: > 80
# Accessibility: > 90
```

---

## Step 9: Complete Launch Checklist (5 min)

### Pre-Launch Verification
- [ ] Backend responding (curl health check)
- [ ] Frontend loading (< 3 seconds)
- [ ] Database connected (psql test)
- [ ] E2E tests passing
- [ ] Payment webhook working
- [ ] Email sending
- [ ] SSL certificates valid
- [ ] Monitoring alerts active
- [ ] Team on standby

### Launch Execution
```bash
# Post to Slack
echo "🚀 SellIA launching to production - https://selldia.app"

# Monitor first 15 minutes
./scripts/health-check.sh 60  # Check every minute for 15 min

# Watch for errors
fly logs -a sellia-api -f | grep -i error

# Check payment processing
psql $DATABASE_URL -c "SELECT COUNT(*) FROM payments WHERE created_at > now() - interval '1 hour';"
```

### Post-Launch
```bash
# Send success message
echo "✅ SellIA live! Revenue flowing, agents working, customers happy"

# Archive deployment log
fly logs -a sellia-api > deployment_$(date +%Y%m%d_%H%M%S).log
```

---

## Rollback Procedure

If critical issue found:

### Immediate Rollback
```bash
# Rollback backend
fly releases -a sellia-api
fly releases rollback <VERSION_ID> -a sellia-api

# Verify
curl https://api.sellia.app/healthz

# Rollback frontend
vercel rollback <DEPLOYMENT_ID>

# Verify
curl https://selldia.app
```

### Full Disaster Recovery
```bash
# Database restore from backup
# 1. Stop application
fly apps stop sellia-api

# 2. Restore database from backup
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier sellia-db-recovered \
  --db-snapshot-identifier sellia-backup-latest

# 3. Update connection string to recovered DB

# 4. Restart application
fly apps open sellia-api
```

---

## Troubleshooting

### Backend won't start
```bash
# Check logs
fly logs -a sellia-api -l error

# Common issues:
# - DATABASE_URL not set → set via: fly secrets set DATABASE_URL=...
# - Migration failed → check alembic error in logs
# - Out of memory → increase VM size: fly scale vm shared-cpu-4x

# Redeploy
fly deploy
```

### API returning 502
```bash
# Check backend processes
fly status -a sellia-api

# Check if it's crashing
fly logs -a sellia-api -l error

# Restart
fly apps restart sellia-api

# If still failing, rollback:
fly releases rollback <VERSION> -a sellia-api
```

### Database too slow
```bash
# Check active connections
psql $DATABASE_URL -c "SELECT COUNT(*) FROM pg_stat_activity;"

# Kill long-running queries
psql $DATABASE_URL -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE duration > '60 seconds';"

# Scale database (if using RDS)
aws rds modify-db-instance --db-instance-identifier sellia-db --db-instance-class db.t3.small
```

### Frontend not connecting to API
```bash
# Check environment variables in Vercel
vercel env list

# Verify CORS settings
curl -X OPTIONS https://api.sellia.app \
  -H "Origin: https://selldia.app" \
  -H "Access-Control-Request-Method: GET"

# Should include:
# Access-Control-Allow-Origin: https://selldia.app
```

---

## Monitoring & Operations

### Daily Health Check
```bash
./scripts/health-check.sh 0

# Should complete with: ✅ All systems nominal
```

### Weekly Maintenance
```bash
# Check error trends
fly logs -a sellia-api -l error | tail -100

# Verify backups
aws rds describe-db-instances --db-instance-identifier sellia-db \
  --query 'DBInstances[0].[BackupRetentionPeriod, LatestRestorableTime]'

# Review performance
# Check Datadog dashboard
```

### Monthly Review
```bash
# Analyze metrics
# - API latency trends
# - Error rate trends
# - Database query performance
# - Revenue per agent
# - Customer retention

# Plan capacity
# - Estimate users in 3 months
# - Plan database scaling
# - Plan CI/CD improvements
```

---

## Support & Escalation

### On-Call Engineer
- Slack: @on-call-engineer
- Email: oncall@selldia.app
- Phone: [number]

### Incident Response
1. Declare incident: Post to #incidents
2. Assign owner: "I'm taking this"
3. Assess impact: "How many users affected?"
4. Root cause: Use logs to understand
5. Fix: Apply patch or rollback
6. Communication: Post updates every 15 min
7. Retrospective: Post-mortem next day

---

## Success Criteria

Deployment is successful when:

✅ Backend health check passing  
✅ Frontend loads in < 3 seconds  
✅ E2E tests all passing  
✅ Payment processing working  
✅ Email sending  
✅ No critical errors  
✅ Customer feedback positive  
✅ Revenue flowing  

**Total Deployment Time:** ~45 minutes  
**Live At:** [Deployment timestamp]  
**First Revenue:** [First transaction timestamp]

---

## Next Steps After Launch

1. **Day 1:** Monitor closely, respond to customer issues
2. **Week 1:** Performance optimization, infrastructure tuning
3. **Month 1:** Feature refinement, scale to handle growth
4. **Quarter 1:** Product roadmap execution, market expansion

---

**Good luck with the launch! 🚀**

Questions? Check the main DEPLOYMENT.md or join #deployments in Slack.
