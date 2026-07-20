# SellIA Production Deployment Guide

Complete step-by-step guide to deploy SellIA to production with backend (Fly.io/Railway/AWS) + frontend (Vercel) + databases.

**Deployment Time: ~45 minutes | Status: Ready for Launch**

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Database Setup](#database-setup)
4. [Backend Deployment](#backend-deployment)
5. [Frontend Deployment](#frontend-deployment)
6. [E2E Testing](#e2e-testing)
7. [Launch Checklist](#launch-checklist)
8. [Rollback Procedures](#rollback-procedures)

---

## Prerequisites

### Required Tools
- **Fly.io CLI** or **Railway CLI** or **AWS CLI** + Docker
- **Vercel CLI**: `npm install -g vercel`
- **Node.js 20+**: `node --version`
- **Python 3.12+**: `python --version`
- **Docker**: `docker --version`
- **PostgreSQL client**: `psql --version`

### Required Accounts
- Fly.io or Railway or AWS account (Backend hosting)
- Vercel account (Frontend hosting)
- Stripe account (Live mode API keys)
- SendGrid account (Email service)
- GitHub account (for CI/CD secrets)

### Credentials to Gather
```
Database:
  - PostgreSQL admin password
  - Redis password

Payment:
  - Stripe live API key (sk_live_...)
  - Stripe webhook secret (whsec_...)
  - Stripe publishable key (pk_live_...)

Email:
  - SendGrid API key

Monitoring:
  - Sentry DSN
  - Datadog API + App key

Hosting:
  - Fly.io/Railway API token
  - Vercel token
  - GitHub secrets access
```

---

## Environment Setup (300L)

### 1. Generate Secure Credentials

```bash
# Generate strong random passwords and keys
python3 scripts/generate-credentials.py

# Output example:
# DB_PASSWORD: x7kL9mP2qR8vN3bJ5cD1eF4gH6iK9oL2
# REDIS_PASSWORD: a1B2c3D4e5F6g7H8i9J0k1L2m3N4o5P6
# SECRET_KEY: q8w7e6r5t4y3u2i1o0p9a8s7d6f5g4h3j2k1l0m9n8b7v6c5x4z3a2s1d0f9g8h7
```

### 2. Create .env.production

Copy the template and fill in values:
```bash
cp .env.production .env.production.local
```

**Critical variables to set:**
```bash
# Database (update with actual values)
DATABASE_URL=postgresql://selliauser:PASSWORD@db-host:5432/selliadb
REDIS_URL=redis://:PASSWORD@redis-host:6379/0

# Secrets
SECRET_KEY=<64-char-random-key>
JWT_SECRET=<random-jwt-key>

# Domain
FRONTEND_URL=https://selldia.app
BACKEND_URL=https://api.selldia.app
CORS_ORIGINS=https://selldia.app,https://www.selldia.app

# Payment (Stripe)
STRIPE_API_KEY=sk_live_YOUR_LIVE_KEY
STRIPE_WEBHOOK_SECRET=whsec_YOUR_WEBHOOK_SECRET
STRIPE_PUBLISHABLE_KEY=pk_live_YOUR_PUBLISHABLE_KEY

# Email (SendGrid)
SENDGRID_API_KEY=SG.YOUR_API_KEY

# Monitoring
SENTRY_DSN=https://YOUR_DSN
DATADOG_API_KEY=YOUR_KEY
DATADOG_APP_KEY=YOUR_APP_KEY

# Feature Flags
ENABLE_COMPUTER_USE=true
ENABLE_WEBHOOK_SIGNATURES=true
```

### 3. Validate Environment Configuration

```bash
# Check all required env vars
python3 scripts/validate-env.py

# Output: ✓ All 45 required environment variables set
```

### 4. Configure Security Headers

```bash
# In backend/.env or hosting platform
SECURE_SSL_REDIRECT=true
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=Strict
X_FRAME_OPTIONS=DENY
X_CONTENT_TYPE_OPTIONS=nosniff
STRICT_TRANSPORT_SECURITY=max-age=31536000
```

### 5. Email Service Setup (SendGrid)

```bash
# Create SendGrid API key
# 1. Visit: https://app.sendgrid.com/settings/api_keys
# 2. Generate new key with Mail Send permission
# 3. Add to secrets: SENDGRID_API_KEY=SG.xxxxx

# Test email sending
python3 -c "
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

mail = Mail(
    from_email='noreply@selldia.app',
    to_emails='test@example.com',
    subject='SellIA Production Test',
    plain_text_content='Email service connected!')
sg = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
sg.send(mail)
print('✓ Email service working')
"
```

### 6. Monitoring Setup

#### Sentry (Error Tracking)
```bash
# 1. Create project at https://sentry.io
# 2. Get DSN: https://xxxxx@xxxxx.ingest.sentry.io/xxxxx
# 3. Add to backend/.env:
SENTRY_DSN=https://xxxxx@xxxxx.ingest.sentry.io/xxxxx

# Verify in backend code (app/core/config.py):
# sentry_sdk.init(dsn=settings.SENTRY_DSN, ...)
```

#### Datadog (Infrastructure Monitoring)
```bash
# 1. Create Datadog account: https://app.datadoghq.com
# 2. Get API key and APP key
# 3. Add to backend environment:
DATADOG_API_KEY=YOUR_API_KEY
DATADOG_APP_KEY=YOUR_APP_KEY

# 4. Deploy Datadog agent to platform
#    For Fly.io: add to fly.toml
#    For Railway: add sidecar service
```

---

## Database Setup (200L)

### 1. Create Production Database Instance

#### Option A: Railway PostgreSQL
```bash
# Connect Railway CLI
railway login

# Create PostgreSQL plugin
railway add

# Select "PostgreSQL" from marketplace
# Copy DATABASE_URL from Railway dashboard

# Test connection
psql $DATABASE_URL -c "SELECT version();"
```

#### Option B: AWS RDS
```bash
# Create RDS instance
aws rds create-db-instance \
  --db-instance-identifier sellia-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username selliauser \
  --master-user-password 'STRONG_PASSWORD' \
  --allocated-storage 100 \
  --backup-retention-period 7

# Wait for instance to be available (10-15 min)
aws rds describe-db-instances --db-instance-identifier sellia-db

# Get endpoint
ENDPOINT=$(aws rds describe-db-instances \
  --db-instance-identifier sellia-db \
  --query 'DBInstances[0].Endpoint.Address' \
  --output text)

# DATABASE_URL=postgresql://selliauser:PASSWORD@$ENDPOINT:5432/selliadb
```

#### Option C: Fly.io Postgres
```bash
# Create Postgres volume and instance
fly postgres create -a sellia-api --name postgres

# Connection string auto-added to fly.toml secrets
```

### 2. Configure Backups

#### Automated Daily Backups
```bash
# Railway: Automatic (7-day retention)
# AWS RDS: Enable in console
# Fly.io: Configure in fly.toml

[http_service]
# ... existing config
[backup]
  enabled = true
  retention_days = 30
  schedule = "02:00 UTC"
```

#### Manual Backup
```bash
# PostgreSQL
pg_dump $DATABASE_URL > backup-$(date +%Y%m%d).sql

# AWS RDS
aws rds create-db-snapshot \
  --db-instance-identifier sellia-db \
  --db-snapshot-identifier sellia-backup-$(date +%Y%m%d)
```

### 3. Run Database Migrations

```bash
# Locally (test)
cd backend-mvp
alembic upgrade head

# In production (via CI/CD)
# fly.toml includes: release_command = "alembic upgrade head"
# This runs automatically during deployment

# Verify migrations
alembic current
alembic history
```

### 4. Create Database Indexes

```sql
-- Connect to production database
psql $DATABASE_URL

-- Create performance indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_sales_user_id ON sales(user_id);
CREATE INDEX idx_sales_created_at ON sales(created_at DESC);
CREATE INDEX idx_analytics_date ON analytics(date DESC);

-- Enable Row-Level Security (RLS)
\i init-rls.sql

-- Verify
SELECT indexname FROM pg_indexes WHERE schemaname = 'public' LIMIT 10;
```

### 5. Setup Monitoring

```bash
# Query monitoring dashboard
psql $DATABASE_URL -c "
SELECT
  datname,
  usename,
  application_name,
  state,
  query
FROM pg_stat_activity
WHERE datname = 'selliadb' AND state = 'active';"

# Set up alerts for:
# - Connection pool exhaustion
# - Query timeout (>10s)
# - Replication lag (>1s)
# - Disk usage (>80%)
```

---

## Backend Deployment (400L)

### Option A: Fly.io Deployment

#### Setup
```bash
# Install Fly CLI
curl -L https://fly.io/install.sh | sh

# Authenticate
fly auth login

# Create app (if not exists)
fly launch --no-deploy --name sellia-api --region gru

# Copy fly.toml to working directory
cp backend-mvp/fly.toml fly.toml
```

#### Set Secrets
```bash
# Add all secrets to Fly
fly secrets set \
  DATABASE_URL='postgresql://...' \
  REDIS_URL='redis://...' \
  SECRET_KEY='...' \
  STRIPE_API_KEY='sk_live_...' \
  SENDGRID_API_KEY='SG.' \
  JWT_SECRET='...' \
  SENTRY_DSN='https://...'

# Verify
fly secrets list
```

#### Deploy
```bash
cd backend-mvp

# Build and deploy
fly deploy --remote-only

# Watch logs
fly logs -a sellia-api

# Check status
fly status

# Verify health check passes
curl https://api.sellia.app/healthz
```

#### Scale (Optional)
```bash
# Increase API replicas
fly scale count api=3

# Increase worker replicas
fly scale count worker=2

# Monitor resource usage
fly scale show
```

---

### Option B: Railway Deployment

#### Setup
```bash
# Install Railway CLI
npm install -g @railway/cli

# Authenticate
railway login

# Initialize project (in backend-mvp)
cd backend-mvp
railway init
```

#### Add Postgres + Redis
```bash
# Add PostgreSQL service
railway add
# Select "PostgreSQL"

# Add Redis service
railway add
# Select "Redis"

# Verify
railway services
```

#### Set Secrets
```bash
# Open dashboard
railway open

# Add environment variables via dashboard:
# DATABASE_URL (auto-set by PostgreSQL plugin)
# REDIS_URL (auto-set by Redis plugin)
# SECRET_KEY, STRIPE_API_KEY, etc. (manual)

# Or via CLI:
railway secrets set SECRET_KEY='...'
railway secrets set STRIPE_API_KEY='sk_live_...'
```

#### Deploy
```bash
# Deploy to Railway
railway up

# View logs
railway logs

# Check deployment status
railway status
```

---

### Option C: AWS Lambda + RDS

#### Package Application
```bash
# Install Serverless Framework
npm install -g serverless

# Configure AWS credentials
aws configure

# Deploy
cd backend-mvp
serverless deploy --stage prod

# Verify function
aws lambda get-function --function-name sellia-api-prod
```

---

### Verification

```bash
# Health check
curl https://api.sellia.app/healthz
# Expected: { "status": "ok", "version": "1.0.0" }

# API test
curl https://api.sellia.app/api/v1/status \
  -H "Authorization: Bearer $TEST_TOKEN"

# Database connectivity
curl https://api.sellia.app/api/v1/health/db
# Expected: { "status": "connected" }

# Check logs for errors
fly logs -a sellia-api | grep -i error
railway logs | grep -i error
aws logs tail /aws/lambda/sellia-api-prod --follow
```

---

## Frontend Deployment (300L)

### Setup

```bash
# Install Vercel CLI
npm install -g vercel

# Authenticate
vercel login

# Navigate to frontend
cd frontend
```

### Link Project

```bash
# Link to Vercel
vercel link

# Follow prompts to select organization and project
# Answers:
# ? Found existing project. Link to it? (Y/n) y
# ? Which scope should contain your project? [your-org]
```

### Set Environment Variables

```bash
# Create .env.production
cat > .env.production << EOF
NEXT_PUBLIC_API_URL=https://api.sellia.app
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_...
NEXT_PUBLIC_ANALYTICS_ID=UA-...
NEXT_PUBLIC_SENTRY_DSN=https://...
EOF

# Add to Vercel via dashboard
vercel env add NEXT_PUBLIC_API_URL production
# Enter: https://api.sellia.app

# Or add via CLI
vercel env add NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY production
```

### Build and Deploy

```bash
# Type check
npx tsc --noEmit --skipLibCheck

# Build
npm run build

# Verify build succeeds
ls .next

# Deploy to production
vercel --prod --yes --token $VERCEL_TOKEN

# Expected output:
# ✅ Production deployment ready [xxxxx.vercel.app]
```

### Domain Configuration

```bash
# Add domain in Vercel dashboard
# 1. Settings → Domains
# 2. Add Domain: selldia.app
# 3. Update DNS records

# Verify SSL
curl -I https://selldia.app
# HTTP/2 200, Certificate: *.vercel.app

# Alternatively, add custom certificate
# in Vercel settings
```

### Verify Frontend

```bash
# Test homepage
curl https://selldia.app

# Check Core Web Vitals
curl https://api.web.dev/pagespeedinsights/v5?url=https://selldia.app&key=$YOUR_API_KEY

# Test API connectivity
curl https://selldia.app/api/health
```

---

## E2E Testing (200L)

### 1. Setup Test Environment

```bash
# Install test dependencies
npm install --save-dev @playwright/test dotenv

# Create .env.test
cat > .env.test << EOF
FRONTEND_URL=https://selldia.app
BACKEND_URL=https://api.sellia.app
TEST_USER_EMAIL=test@selldia.app
TEST_USER_PASSWORD=SecureTestPassword123!
EOF
```

### 2. Critical Path Tests

Run tests against production:

```bash
# Test 1: Login Flow
npm run test:e2e -- tests/e2e_tests.spec.ts -g "Login"

# Test 2: Market Detection
npm run test:e2e -- tests/e2e_tests.spec.ts -g "Market detection"

# Test 3: Strategy Selection
npm run test:e2e -- tests/e2e_tests.spec.ts -g "Strategy"

# Test 4: Payment Processing
npm run test:e2e -- tests/e2e_tests.spec.ts -g "Payment"

# Test 5: Dashboard Data
npm run test:e2e -- tests/e2e_tests.spec.ts -g "Dashboard"

# Run all
npm run test:e2e
```

### 3. Verify API

```bash
# Health endpoint
curl -s https://api.sellia.app/healthz | jq .

# Metrics endpoint
curl -s https://api.sellia.app/metrics | head -20

# API response time
time curl -s https://api.sellia.app/api/v1/status > /dev/null

# Expected: <200ms
```

### 4. Test Webhooks

```bash
# Stripe webhook test
curl -X POST https://api.sellia.app/webhooks/stripe \
  -H "Content-Type: application/json" \
  -H "Stripe-Signature: test_signature" \
  -d '{
    "type": "payment_intent.succeeded",
    "data": {"object": {"id": "pi_test"}}
  }'

# Expected: 200 OK

# Check webhook logs
fly logs -a sellia-api | grep -i webhook
```

### 5. Email Delivery

```bash
# Send test email
curl -X POST https://api.sellia.app/api/v1/emails/send \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "to": "test@example.com",
    "subject": "SellIA Production Test",
    "template": "welcome"
  }'

# Check SendGrid dashboard for delivery confirmation
# https://mail.google.com/mail/u/0/#search/noreply%40selldia.app
```

### 6. Performance Benchmarks

```bash
# Load test API (5 concurrent users, 30 sec)
ab -n 1000 -c 5 https://api.sellia.app/api/v1/status

# Expected results:
# Requests/sec: >100
# Mean latency: <50ms
# 95th percentile: <200ms

# Frontend performance
lighthouse https://selldia.app --output-path=report.html

# Expected scores:
# Performance: >80
# Accessibility: >90
# Best Practices: >90
# SEO: >90
```

---

## Launch Checklist (100L)

### Pre-Launch (Day -1)

- [ ] All environment variables set in production
- [ ] Database backups configured and tested
- [ ] SSL certificates valid and auto-renewing
- [ ] Monitoring alerts active (Sentry, Datadog)
- [ ] Monitoring dashboards created
- [ ] On-call team briefed and rotation set up
- [ ] Runbooks documented
- [ ] Rollback procedure tested
- [ ] Communication template prepared
- [ ] Support team trained

### Launch Morning

- [ ] Backend health checks passing
- [ ] Frontend building and deploying successfully
- [ ] E2E tests all green
- [ ] Payment processing verified (test transaction)
- [ ] Email sending verified
- [ ] API response times <200ms
- [ ] Database connections stable
- [ ] Monitoring collecting data
- [ ] Alerts testing (send test alert)
- [ ] DNS pointing to production

### Launch Execution

- [ ] Post announcement in #launches Slack
- [ ] Monitor error rates (target: <0.1%)
- [ ] Monitor API latency (target: <100ms p50, <500ms p99)
- [ ] Monitor database connections
- [ ] Check Sentry for new errors
- [ ] Verify payment transactions are processing
- [ ] Monitor email delivery success rate
- [ ] Check user feedback channels

### Post-Launch (Hour 1)

- [ ] Verify all metrics nominal
- [ ] Check for any alerts
- [ ] Confirm no customer-impacting errors
- [ ] Review Sentry error log
- [ ] Post update: "✅ SellIA live and stable"

---

## Rollback Procedures

### Quick Rollback (< 5 minutes)

#### Fly.io
```bash
# List recent deployments
fly releases -a sellia-api

# Rollback to previous version
fly releases rollback <VERSION_ID> -a sellia-api

# Verify health
curl https://api.sellia.app/healthz
```

#### Railway
```bash
# Rollback via dashboard or CLI
railway rollback

# Verify
railway status
```

#### Frontend (Vercel)
```bash
# Rollback to previous deployment
vercel rollback <DEPLOYMENT_ID>

# Or via dashboard: Settings > Deployments
```

### Database Rollback

```bash
# Restore from backup
# WARNING: This loses data since backup

# AWS RDS
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier sellia-db-rollback \
  --db-snapshot-identifier sellia-backup-2024xxxx

# PostgreSQL
psql $DATABASE_URL < backup-20240603.sql
```

### Full Rollback Procedure

If critical bug found:

1. **Immediate (0-5 min)**
   - Rollback backend to previous deploy
   - Rollback frontend to previous deploy
   - Verify health endpoints respond
   - Post to #incidents: "Incident declared: [issue description]"

2. **First Response (5-30 min)**
   - Assess customer impact
   - Check error logs
   - Identify root cause
   - Notify affected users
   - Document issue

3. **Fix & Redeploy (30+ min)**
   - Fix the bug
   - Run tests locally
   - Deploy to staging
   - Run E2E tests
   - Deploy to production
   - Monitor for 10 minutes

---

## Production Runbook

### Daily Checks

```bash
#!/bin/bash
# Daily production health check

echo "🔍 Checking SellIA Production Status..."

# API health
echo -n "API Health: "
curl -s https://api.sellia.app/healthz | jq -r '.status' || echo "FAIL"

# Database connections
echo -n "DB Connections: "
curl -s https://api.sellia.app/api/v1/health/db | jq -r '.active_connections' || echo "FAIL"

# Recent errors (Sentry)
echo -n "Sentry Issues (24h): "
curl -s https://api.sentry.io/api/0/organizations/YOUR_ORG/issues/\
  -H "Authorization: Bearer $SENTRY_TOKEN" \
  | jq '.[] | select(.lastSeen | . > (now - 86400)) | .shortId' | wc -l

# Payment success rate
echo -n "Payment Success Rate: "
curl -s https://api.sellia.app/api/v1/metrics/payments/success-rate \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq '.rate'

echo "✅ Daily checks complete"
```

### Common Issues & Fixes

| Issue | Solution |
|-------|----------|
| API returning 502 | Check backend logs, restart containers, check database connection |
| Slow API responses | Check database query performance, scale API instances |
| Payment failures | Check Stripe webhook, verify API key, check database audit_log |
| Email not sending | Check SendGrid API key, verify email address format, check delivery |
| High error rate | Check Sentry, revert latest deploy, check database migrations |

---

## Support & Monitoring

### Monitoring Dashboards

- **Fly.io**: https://fly.io/apps/sellia-api
- **Railway**: https://railway.app/project/...
- **Vercel**: https://vercel.com/projects/...
- **Sentry**: https://sentry.io/organizations/...
- **Datadog**: https://app.datadoghq.com

### Alert Channels

- **Slack**: #incidents, #deployments, #alerts
- **PagerDuty**: On-call rotation
- **Email**: ops@selldia.app

### Escalation Contacts

- **On-Call Engineer**: [rotate team contact]
- **Engineering Manager**: [manager email]
- **CEO**: [ceo email]

---

## Success Criteria

Deployment is successful when:

- ✅ All health checks passing
- ✅ API responding <200ms avg
- ✅ Zero customer-facing errors
- ✅ Payment processing working
- ✅ Emails delivering successfully
- ✅ All E2E tests passing
- ✅ No alerts triggered
- ✅ Monitoring data flowing
- ✅ Users logging in successfully
- ✅ Sales agent making real decisions

---

**Deployment Status: READY FOR PRODUCTION LAUNCH**

Last Updated: 2024-06-03
Deployment Lead: [Name]
Approved By: [CEO/CTO]
