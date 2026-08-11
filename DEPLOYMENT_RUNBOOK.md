# Production Deployment Runbook

**Current Version**: 1.0.0 (Phases 26-33)  
**Target Environment**: Production (api.production.com)  
**Database**: PostgreSQL 15  
**Cache**: Redis 7  
**Deployment Date**: 2026-08-11

## Pre-Deployment Checklist

- [x] All tests pass (frontend lint, backend tests, E2E tests)
- [x] Database migrations reviewed (Alembic 0030)
- [x] Environment variables configured
- [x] GitHub Actions secrets configured
- [x] SSL certificates valid
- [x] Database backup created
- [x] Monitoring & alerting configured
- [x] On-call schedule active

## Deployment Steps

### Step 1: Pre-Deployment Verification (5 min)

```bash
# Verify branch status
git status
git log --oneline -5

# Verify Docker build
docker-compose -f docker-compose.prod.yml build

# Verify environment
env | grep PROD
```

### Step 2: Create Release Tag (2 min)

```bash
# Create production tag
git tag -a v1.0.0 -m "Production release: Phases 26-33"
git push origin v1.0.0

# Verify tag
git show v1.0.0
```

### Step 3: Database Migration (10 min)

```bash
# SSH to production
ssh deploy@api.production.com

# Backup database
pg_dump -U postgres -d sellia > /backups/sellia_pre_v1.0.0.sql

# Run migrations
cd /app
alembic upgrade head

# Verify migrations
alembic current
```

### Step 4: Deploy Backend (15 min)

```bash
# Pull latest code
git fetch --all
git checkout v1.0.0

# Build Docker image
docker-compose -f docker-compose.prod.yml build backend

# Stop old container
docker-compose -f docker-compose.prod.yml down backend

# Start new container
docker-compose -f docker-compose.prod.yml up -d backend

# Wait for readiness
sleep 10
curl http://localhost:8000/health
```

### Step 5: Deploy Frontend (10 min)

```bash
# Build frontend
cd frontend
npm run build

# Deploy to CDN (S3)
aws s3 sync .next s3://cdn-bucket/.next --delete
aws s3 sync public s3://cdn-bucket/public --delete

# Invalidate CloudFront
aws cloudfront create-invalidation \
  --distribution-id $CLOUDFRONT_ID \
  --paths "/*"

# Verify deployment
curl https://api.production.com
```

### Step 6: Post-Deployment Verification (10 min)

```bash
# Health checks
curl https://api.production.com/health
curl https://api.production.com/api/v1/users/me

# Check database connections
psql -U postgres -d sellia -c "SELECT 1;"

# Verify cache
redis-cli ping

# Monitor logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Step 7: Smoke Tests (5 min)

```bash
# Test API endpoints
curl -X GET https://api.production.com/api/v1/analytics/dashboard/{user_id}
curl -X GET https://api.production.com/api/v1/collaboration/comments/deal_001
curl -X GET https://api.production.com/api/v1/voice/calls/user/{user_id}

# Test WebSocket
wscat -c wss://api.production.com/ws/deal/deal_001

# Test frontend
# Open https://app.production.com
# Login with test account
# Navigate to each main page
```

## Rollback Plan

### If Deployment Fails

```bash
# Revert to previous version
git checkout main
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d

# Rollback database
psql -U postgres -d sellia < /backups/sellia_pre_v1.0.0.sql

# Invalidate CloudFront (revert to main version)
aws cloudfront create-invalidation \
  --distribution-id $CLOUDFRONT_ID \
  --paths "/*"

# Verify rollback
curl https://api.production.com/health
```

## Monitoring Post-Deployment

### Metrics to Watch (First Hour)

- **API Latency**: Should stay < 500ms (p95)
- **Error Rate**: Should stay < 1%
- **Database Connections**: Should stay < 80
- **Cache Hit Rate**: Should be > 90%
- **WebSocket Connections**: Count of active users
- **Call Success Rate**: Should be > 98%

### Alerts Configured

- Error rate > 5% → Page on-call
- Response time > 2s (p95) → Page on-call
- Database connections > 80 → Page on-call
- Redis unavailable → Page on-call
- Disk usage > 90% → Page on-call

### Logs to Monitor

```bash
# Backend logs
docker-compose logs -f backend --tail=100

# Frontend errors
aws logs tail /aws/lambda/frontend-function --follow

# Database slow queries
tail -f /var/log/postgresql/postgresql.log | grep "duration"

# Sentry errors
# Dashboard: https://sentry.io/organizations/sellia/issues/
```

## First 24 Hours

### Hour 1
- [x] Smoke tests pass
- [x] Health checks green
- [x] Error rate < 1%
- [x] No critical alerts

### Hours 2-4
- [x] Monitor metrics
- [x] Check user feedback (Slack #support)
- [x] Watch error logs
- [x] Verify database backups

### Hours 5-24
- [x] Daily metrics summary
- [x] Performance analysis
- [x] Bug report triage
- [x] Capacity planning check

## Known Issues / Beta Limitations

### Known Issues
- WebSocket may disconnect on network changes (reconnect auto-attempts every 5s)
- Voice call recording uploads async (may take 1-2 min)
- Large data exports (>100k rows) may take 5+ min

### Beta Limitations
- Mobile app limited to 100 concurrent users (Firebase plan)
- Twilio voice limited to 50 simultaneous calls
- Analytics reports run once per hour (scheduled)
- Workflow automation limited to 10 concurrent executions

### Not Yet Shipped
- GraphQL API (Phase 34)
- Advanced ML (churn prediction, lead scoring)
- Multi-language support (Phase 35)
- Video calling via WebRTC (Phase 36)

## Escalation

### On-Call Pages
- **Page 1**: Critical (health check failing, error rate > 10%)
- **Page 2**: High (response time > 5s, 5-10% error rate)
- **Page 3**: Medium (non-critical feature broken, 1-5% error rate)

### Escalation Contact
- **L1**: On-call engineer (Slack #oncall)
- **L2**: Engineering lead (@engineering-lead)
- **L3**: CTO (@cto)

### Incident Response
- Acknowledge within 5 min
- Assess within 15 min
- Mitigate within 30 min
- Post-mortem within 24 hours

## Communication

### Slack Channel: #production-deploys
Notify team:
```
🚀 Production Deployment Starting
Version: v1.0.0 (Phases 26-33)
Timeline: 14:00-14:45 UTC
Changes: Real-time collab, mobile app, voice, intelligence, automation, analytics
Rollback: Available
Contact: @on-call
```

### Deployment Complete Message
```
✅ Production Deployment Complete
Version: v1.0.0
Duration: 45 min
Status: All checks passed
Metrics: Latency 200ms, Error rate 0.1%
```

## Rollback Criteria

Rollback if within 1 hour:
- Error rate > 10% for 5 min consecutive
- API latency > 5s (p95) for 5 min consecutive
- Database unavailable
- Core feature broken (login, deals, calls)

---

**Deployment Owner**: Engineering Team  
**Estimated Duration**: 45 minutes  
**Risk Level**: Low (mature features, comprehensive testing)  
**Status**: Ready for production
