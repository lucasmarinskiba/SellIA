# SellIA Production Launch Checklist

**Launch Date:** [DATE]  
**Deployment Lead:** [NAME]  
**CEO Approval:** [SIGNATURE]  
**Status:** 🚀 READY FOR PRODUCTION

---

## Pre-Launch (Day -1, 4 PM)

### Infrastructure & Hosting
- [ ] Fly.io account created and app configured (`sellia-api`)
- [ ] Database (PostgreSQL) provisioned and tested
- [ ] Redis cache provisioned and tested
- [ ] Vercel project created and linked to GitHub
- [ ] DNS domains pointing to production (selldia.app, api.sellia.app)
- [ ] SSL certificates active (auto-renew enabled)
- [ ] CDN configured (Vercel Edge Network active)

### Secrets & Credentials
- [ ] `.env.production` created with all required variables
- [ ] Credentials script run: `python3 scripts/generate-credentials.py`
- [ ] All secrets added to hosting platform:
  - [ ] Fly.io secrets: DATABASE_URL, REDIS_URL, SECRET_KEY, STRIPE_API_KEY, etc.
  - [ ] Vercel env vars: NEXT_PUBLIC_API_URL, analytics keys, feature flags
  - [ ] GitHub secrets: VERCEL_TOKEN, FLY_API_TOKEN, etc.
- [ ] `.env.production` file added to `.gitignore` (verified not committed)
- [ ] Credential file permissions: 600 (only readable by owner)

### Database Setup
- [ ] PostgreSQL production instance created
- [ ] Database created: `selliadb`
- [ ] User created: `selliauser` with strong password
- [ ] Connection pooling configured (pool_size=20)
- [ ] Backups enabled (daily, 30-day retention)
- [ ] Backup tested (restore procedure validated)
- [ ] Row-Level Security (RLS) enabled via `init-rls.sql`
- [ ] Performance indexes created
- [ ] Replication configured (if using Multi-AZ)

### Payment Processing
- [ ] Stripe account in Live mode (not test mode)
- [ ] Stripe live API key verified (starts with `sk_live_`)
- [ ] Stripe webhook configured:
  - [ ] Endpoint: `https://api.sellia.app/webhooks/stripe`
  - [ ] Events: payment_intent.succeeded, payment_intent.payment_failed
  - [ ] Signature verified in code
- [ ] Stripe webhook secret saved to environment
- [ ] Test payment processed and verified
- [ ] Payment confirmation email sent correctly

### Email Service
- [ ] SendGrid account created
- [ ] SendGrid API key generated (Mail Send permission only)
- [ ] Sender email verified: `noreply@selldia.app`
- [ ] Email templates created:
  - [ ] Welcome email
  - [ ] Payment confirmation
  - [ ] Sales agent summary
  - [ ] Weekly digest
- [ ] Email deliverability tested
- [ ] SPF/DKIM/DMARC records configured

### Monitoring & Logging
- [ ] Sentry account created
- [ ] Sentry DSN added to backend
- [ ] Sentry release tracking configured
- [ ] Error rate alerting enabled (threshold: 1%)
- [ ] Datadog account created (if using)
- [ ] Datadog agent deployed
- [ ] Log aggregation configured (backend logs → Datadog)
- [ ] Custom dashboards created:
  - [ ] API latency p50/p95/p99
  - [ ] Error rate by endpoint
  - [ ] Database connections
  - [ ] Payment success rate
- [ ] Alert rules created for:
  - [ ] API returning 5xx (> 5 errors/min)
  - [ ] Database connection pool exhausted
  - [ ] Payment webhook failures
  - [ ] High latency (p99 > 1000ms)
  - [ ] High error rate (> 1%)

### Security & Compliance
- [ ] Security headers configured:
  - [ ] SECURE_SSL_REDIRECT=true
  - [ ] SESSION_COOKIE_SECURE=true
  - [ ] SESSION_COOKIE_HTTPONLY=true
  - [ ] SESSION_COOKIE_SAMESITE=Strict
  - [ ] X-Frame-Options: DENY
  - [ ] X-Content-Type-Options: nosniff
  - [ ] Strict-Transport-Security: max-age=31536000
- [ ] Rate limiting enabled (60 req/min per IP)
- [ ] CORS configured for selldia.app only
- [ ] API key rotation procedure documented
- [ ] Security scanning enabled (GitHub/Snyk)
- [ ] GDPR compliance verified:
  - [ ] Data processing agreement reviewed
  - [ ] Privacy policy updated
  - [ ] Cookie consent implemented
- [ ] Encryption enabled (TLS 1.3 minimum)
- [ ] Password requirements validated (12+ chars, complexity)

### Team & Documentation
- [ ] Deployment runbook documented (`DEPLOYMENT.md`)
- [ ] Rollback procedure tested and documented
- [ ] Health check script created and tested
- [ ] On-call rotation established
- [ ] Escalation contacts confirmed:
  - [ ] Engineering Lead: [NAME] ([EMAIL])
  - [ ] CEO: [NAME] ([EMAIL])
  - [ ] Customer Support: [EMAIL]
- [ ] Support team trained on:
  - [ ] Common customer issues
  - [ ] Payment troubleshooting
  - [ ] Feature walkthrough
- [ ] Customer communication template prepared
- [ ] Launch announcement prepared

### Build & Test
- [ ] Backend Docker image builds successfully
- [ ] Backend passes linting: `npm run lint`
- [ ] Backend tests pass: `npm run test`
- [ ] Frontend builds successfully: `npm run build`
- [ ] Frontend passes type checking: `tsc --noEmit`
- [ ] E2E tests pass (staging): `npm run test:e2e:staging`
- [ ] Performance tests pass:
  - [ ] API latency < 200ms p50
  - [ ] Frontend Core Web Vitals > 80
  - [ ] Cold start < 3 seconds
- [ ] Load test results acceptable:
  - [ ] 100 concurrent users
  - [ ] Error rate < 0.1%
  - [ ] p99 latency < 1000ms

---

## Launch Day Morning (8 AM - 12 PM)

### Final Infrastructure Checks
- [ ] Database connection pooling working
- [ ] Redis cache responding
- [ ] Backup system operational
- [ ] Monitoring dashboards live
- [ ] Log streaming to Datadog working
- [ ] DNS records propagated (check with `dig api.sellia.app`)
- [ ] SSL certificates valid (check with `openssl s_client`)

### Backend Deployment
- [ ] Backend deployed to production with `fly deploy`
- [ ] Release command executed (database migrations)
- [ ] Health checks passing:
  - [ ] `curl https://api.sellia.app/healthz` → 200 OK
  - [ ] Response time < 200ms
  - [ ] Database connection confirmed
- [ ] Logs show no errors in first 5 minutes
- [ ] Metrics starting to flow to Datadog
- [ ] API responding to real requests

### Frontend Deployment
- [ ] Frontend deployed to Vercel with `vercel --prod`
- [ ] Homepage loads in < 3 seconds
- [ ] API connectivity verified
- [ ] Analytics script loaded
- [ ] Feature flags initialized
- [ ] Service worker registered (offline support)
- [ ] Static assets cached correctly

### E2E Test Execution (Production)
- [ ] Login flow working:
  - [ ] Create account
  - [ ] Verify email (check inbox)
  - [ ] Login with credentials
  - [ ] Session persists
- [ ] Market detection working:
  - [ ] Create new agent
  - [ ] Agent analyzes market
  - [ ] Market data accurate
- [ ] Strategy selection working:
  - [ ] Agent selects appropriate strategy
  - [ ] Strategy parameters reasonable
- [ ] Payment processing working:
  - [ ] Create order
  - [ ] Stripe charge created
  - [ ] Webhook received and recorded
  - [ ] Confirmation email sent
  - [ ] Dashboard updated
- [ ] Dashboard data:
  - [ ] Sales metrics displayed
  - [ ] Agent performance visible
  - [ ] Charts loading correctly
  - [ ] Export working

### Data Integrity
- [ ] Database constraints verified
- [ ] Foreign keys intact
- [ ] No orphaned records
- [ ] Indexes built successfully
- [ ] Replication lag < 1 second (if using)

### Webhook Testing
- [ ] Stripe webhooks being received
- [ ] Webhook logs visible
- [ ] Payment confirmed emails sending
- [ ] Payment status updating in database

### External Service Connectivity
- [ ] Stripe API responding
- [ ] SendGrid API responding
- [ ] Sentry receiving events
- [ ] Datadog collecting metrics
- [ ] Google Analytics tracking visits

---

## Launch Execution (12 PM - 1 PM)

### Go/No-Go Decision
- [ ] All pre-flight checks passed
- [ ] Team confident in readiness
- [ ] Business stakeholder approval given
- [ ] **GO DECISION**: ✅ **APPROVED TO LAUNCH**

### Launch Execution
- [ ] Post to Slack: "🚀 SellIA launching to production"
- [ ] Customer announcement posted
- [ ] Monitoring dashboards open
- [ ] Team on standby in Slack #launches channel
- [ ] Error tracking active (Sentry)
- [ ] Metrics flowing (Datadog)

### Immediate Monitoring (First 15 minutes)
- [ ] No critical errors in Sentry
- [ ] API latency nominal (< 200ms p50)
- [ ] Database connections healthy
- [ ] Payment transactions processing
- [ ] Email deliveries succeeded
- [ ] No customer complaints (check email/support)
- [ ] Revenue metrics incrementing

### 30-Minute Check
- [ ] Error rate < 0.1%
- [ ] All E2E tests still passing
- [ ] Customer feedback positive
- [ ] Performance metrics stable
- [ ] Payment success rate > 99%

### 1-Hour Check
- [ ] No critical issues identified
- [ ] Feature utilization metrics look correct
- [ ] Database performance acceptable
- [ ] No security alerts triggered
- [ ] Team confidence high

### Announcement
- [ ] Post update: "✅ SellIA successfully launched to production"
- [ ] Share metrics in #launches
- [ ] Thank team in Slack
- [ ] Send customer success email

---

## Post-Launch (Day 1 - End of Day)

### Production Monitoring
- [ ] Error tracking working
- [ ] Metrics being collected
- [ ] Logs accessible
- [ ] Alerts functioning correctly
- [ ] No false positives

### Customer Engagement
- [ ] Customers successfully using platform
- [ ] Support tickets monitored
- [ ] Feedback channels monitored
- [ ] Performance meeting expectations
- [ ] Payment processing reliable

### Documentation
- [ ] Deployment log created
- [ ] Incident report (if any) documented
- [ ] Lessons learned documented
- [ ] Runbook updated
- [ ] On-call procedures tested

### Team Debrief
- [ ] Team meeting scheduled (Day 2)
- [ ] Launch retrospective prepared
- [ ] Post-mortems (if needed) scheduled
- [ ] Celebration planned

### Monitoring Setup
- [ ] Team trained on dashboards
- [ ] Alert routing configured
- [ ] On-call schedule active
- [ ] Incident response tested
- [ ] Escalation procedure practiced

---

## Post-Launch (Week 1)

### Stability Monitoring
- [ ] Error rate remains < 0.1%
- [ ] All endpoints performing well
- [ ] Database queries optimized
- [ ] No memory leaks detected
- [ ] Log volume reasonable
- [ ] Infrastructure scaling properly

### Customer Success
- [ ] Onboarding successful
- [ ] Feature adoption metrics positive
- [ ] Support tickets at acceptable level
- [ ] Customer satisfaction high
- [ ] Feature requests collected

### Performance Analysis
- [ ] Analyze API latency trends
- [ ] Review database performance
- [ ] Optimize slow queries (if any)
- [ ] Review error patterns
- [ ] Capacity planning for growth

### Security Validation
- [ ] HTTPS working correctly
- [ ] Authentication working
- [ ] Authorization rules enforced
- [ ] Data validation working
- [ ] Security headers present

### Backup Verification
- [ ] Backup completed successfully
- [ ] Backup restoration tested
- [ ] Recovery time objective (RTO) validated
- [ ] Recovery point objective (RPO) validated

---

## Post-Launch (Month 1)

### Performance Review
- [ ] Performance metrics analyzed
- [ ] Bottlenecks identified and fixed
- [ ] Scaling needs assessed
- [ ] Cost optimization opportunities identified
- [ ] Revenue targets being met

### Feature Adoption
- [ ] Primary features adopted
- [ ] Secondary features identified
- [ ] User engagement metrics strong
- [ ] Retention rate acceptable

### Operational Excellence
- [ ] Runbooks refined
- [ ] Monitoring optimized
- [ ] Alert fatigue eliminated
- [ ] On-call experience positive
- [ ] Team confidence high

---

## Sign-Off

**Deployment Lead:** _________________ **Date:** _______

**Engineering Manager:** _________________ **Date:** _______

**CEO/Founder:** _________________ **Date:** _______

**Customer Success Lead:** _________________ **Date:** _______

---

**Launch Status: 🚀 LIVE IN PRODUCTION**

Deployment Time: ~45 minutes  
Live At: [TIMESTAMP]  
First Transaction At: [TIMESTAMP]  
Revenue Generated: [AMOUNT]
