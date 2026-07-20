# SellIA Production Deployment Checklist

Complete checklist for deploying SellIA to production. Use this to ensure all components are properly configured.

## Pre-Deployment (1-2 weeks before)

### Infrastructure Setup
- [ ] AWS/GCP/Azure account created and configured
- [ ] VPC/network setup complete
- [ ] Security groups/firewall rules configured
- [ ] Load balancer provisioned
- [ ] CDN configured (Cloudflare/AWS CloudFront)
- [ ] Database provider selected and account created
- [ ] Redis provider selected and account created

### SSL/TLS Certificates
- [ ] Domain registered and DNS configured
- [ ] SSL certificate obtained (Let's Encrypt recommended)
- [ ] Certificate uploaded to load balancer
- [ ] Auto-renewal configured
- [ ] Backup certificates prepared

### Third-Party Services
- [ ] Stripe account created and API keys obtained
- [ ] MercadoPago account configured
- [ ] SendGrid account set up with verified domain
- [ ] Datadog/Sentry accounts created
- [ ] GitHub Actions secrets configured
- [ ] Slack webhook configured for notifications

### Documentation
- [ ] Architecture diagram created
- [ ] Runbooks documented
- [ ] Incident response procedures written
- [ ] On-call schedule established
- [ ] Team trained on deployment process

## 1 Week Before Deployment

### Code Preparation
- [ ] All feature branches merged to main
- [ ] Code review completed
- [ ] Linting checks pass
- [ ] Unit tests passing (>80% coverage)
- [ ] Integration tests passing
- [ ] E2E tests passing
- [ ] Security audit completed
- [ ] Dependencies up to date

### Environment Configuration
- [ ] .env.production file created with all secrets
- [ ] Secrets stored securely (AWS Secrets Manager, HashiCorp Vault)
- [ ] Database credentials generated and secured
- [ ] Redis password generated
- [ ] JWT secret generated
- [ ] API keys stored securely
- [ ] Backup encryption key created

### Database Preparation
- [ ] PostgreSQL database created
- [ ] Database user with minimal required permissions created
- [ ] Initial schema migrations prepared
- [ ] Backup location configured
- [ ] Backup retention policy set
- [ ] Test restore procedure executed

### Monitoring Setup
- [ ] Datadog agent configured
- [ ] Sentry project created
- [ ] CloudWatch log groups created
- [ ] Prometheus/Grafana dashboards created
- [ ] Alert rules configured
- [ ] PagerDuty integration set up
- [ ] Slack channels created (#incidents, #alerts, #deployments)

## Day Before Deployment

### Final Code Review
- [ ] Production build created and tested
- [ ] Docker images built and pushed to registry
- [ ] Container security scan passed
- [ ] Dependency scan completed

### Database Readiness
- [ ] Database connection tested
- [ ] Migrations tested on staging environment
- [ ] Backup verified
- [ ] Backup restoration tested
- [ ] Database performance baseline established

### Infrastructure Validation
- [ ] All services accessible
- [ ] Load balancer health checks passing
- [ ] CDN cache cleared/configured
- [ ] DNS propagation confirmed
- [ ] SSL certificate validity confirmed
- [ ] Network connectivity tested

### Communication
- [ ] Deployment window announced to team
- [ ] Stakeholders informed
- [ ] Maintenance window announced if needed
- [ ] On-call engineer assigned
- [ ] Emergency contacts list prepared

## Deployment Day

### Pre-Deployment (2 hours before)

Operations
- [ ] Team ready and online
- [ ] All tools operational
- [ ] Slack channels active
- [ ] Monitoring dashboards open
- [ ] Incident response plan reviewed
- [ ] Rollback plan confirmed

Database
- [ ] Fresh backup taken
- [ ] Backup verified
- [ ] Database connection tested
- [ ] Connection pool configured
- [ ] Replication status checked (if applicable)

Infrastructure
- [ ] Load balancer ready
- [ ] All servers healthy
- [ ] CDN cache cleared
- [ ] SSL certificates valid
- [ ] DNS still resolving correctly

### Deployment Execution (During)

1. Database Migrations
   - [ ] Run migrations on staging first
   - [ ] Verify migrations successful
   - [ ] Run migrations on production
   - [ ] Confirm all tables/indexes created
   - [ ] Monitor migration progress

2. Backend Deployment
   - [ ] Pull latest code
   - [ ] Build Docker images
   - [ ] Push images to registry
   - [ ] Update ECS/K8s task definitions
   - [ ] Deploy to production (rolling update)
   - [ ] Monitor deployment progress
   - [ ] Verify all pods/containers running
   - [ ] Health checks passing
   - [ ] No error rate spike
   - [ ] Response times normal

3. Frontend Deployment
   - [ ] Pull latest code
   - [ ] Run build
   - [ ] Push to Vercel/CDN
   - [ ] Verify deployment successful
   - [ ] Cache invalidation complete
   - [ ] Frontend loads correctly
   - [ ] No console errors

4. Smoke Tests
   - [ ] API health check passing
   - [ ] Database connection working
   - [ ] Redis connection working
   - [ ] Login flow working
   - [ ] Basic user flows operational
   - [ ] Payment processing functional
   - [ ] Email sending working
   - [ ] Error logging active

5. Monitoring
   - [ ] Metrics showing normal values
   - [ ] Error rate at baseline
   - [ ] Response times stable
   - [ ] No unexpected alerts
   - [ ] System resources healthy
   - [ ] Database queries efficient

### Post-Deployment (1 hour after)

Validation
- [ ] All critical features tested
- [ ] User can complete full workflow
- [ ] No data loss occurred
- [ ] Performance meets SLAs
- [ ] Error logs reviewed
- [ ] Security vulnerabilities none detected

Monitoring
- [ ] Dashboards show normal operation
- [ ] All alerts resolved
- [ ] No performance degradation
- [ ] Load distribution even across instances
- [ ] Resource utilization normal

Communication
- [ ] Stakeholders notified of success
- [ ] Status page updated
- [ ] Team debriefing scheduled
- [ ] Documentation updated with actual times/results

### If Issues Encountered

Troubleshooting
- [ ] Issue logged in incident tracking
- [ ] On-call engineer engaged
- [ ] Issue severity assessed
- [ ] Rollback decision made if necessary

Rollback (if needed)
- [ ] Stop deployments
- [ ] Revert to previous version
- [ ] Monitor rollback progress
- [ ] Verify system stable on previous version
- [ ] Root cause analysis started
- [ ] Team debriefing scheduled

## Post-Deployment (Next 24 hours)

### Monitoring
- [ ] Continuous monitoring for 24 hours
- [ ] Daily error log review
- [ ] Performance trending analysis
- [ ] User feedback collection
- [ ] Security event review

### Documentation
- [ ] Deployment notes recorded
- [ ] Any deviations from plan documented
- [ ] Lessons learned captured
- [ ] Runbook updates made
- [ ] Training materials updated

### Optimization
- [ ] Monitor for slow queries
- [ ] Review database performance
- [ ] Check cache hit rates
- [ ] Analyze CDN effectiveness
- [ ] Identify bottlenecks

### Team
- [ ] Debrief meeting held
- [ ] Successes acknowledged
- [ ] Issues discussed and resolved
- [ ] Improvements documented
- [ ] Training gaps identified

## Ongoing (Weekly/Monthly)

### Monitoring
- [ ] Check all alert thresholds appropriate
- [ ] Review error rates and trends
- [ ] Validate SLA compliance
- [ ] Monitor resource utilization
- [ ] Check backup integrity

### Security
- [ ] Review security logs
- [ ] Update firewall rules if needed
- [ ] Rotate API keys
- [ ] Verify SSL certificates
- [ ] Security audit results reviewed

### Maintenance
- [ ] Database optimization
- [ ] Dependency updates
- [ ] Backup restoration testing
- [ ] Disaster recovery drills
- [ ] Performance tuning

### Communication
- [ ] Status reports generated
- [ ] Team knowledge sharing
- [ ] Customer communication about new features
- [ ] Documentation kept current

## Deployment Success Criteria

All of the following must be true for deployment to be considered successful:

1. **Functionality**
   - All critical user paths working
   - No data loss or corruption
   - All integrations operational

2. **Performance**
   - API P95 latency < 200ms
   - P99 latency < 500ms
   - Frontend load time < 3 seconds
   - Error rate < 0.1%

3. **Reliability**
   - 99.9% uptime
   - Database connections stable
   - No memory leaks
   - No CPU spikes

4. **Security**
   - No new vulnerabilities
   - SSL/TLS working
   - Rate limiting active
   - Audit logs being recorded

5. **Monitoring**
   - All metrics collected
   - Alerts functioning
   - Logs aggregated
   - Dashboards updated

## Emergency Contacts

- **On-Call Engineer:** [Name, Phone, Email]
- **Database Admin:** [Name, Phone, Email]
- **Infrastructure Team:** [Name, Phone, Email]
- **CTO/Tech Lead:** [Name, Phone, Email]
- **Incident Commander:** [Name, Phone, Email]

## Deployment Timeline (Typical)

- T-2 weeks: Infrastructure setup
- T-1 week: Code finalization, monitoring setup
- T-24h: Final validation, team preparation
- T-0: Deployment execution (2-4 hours)
- T+1h: Post-deployment validation
- T+24h: Continuous monitoring
- T+1 week: Debrief and optimization

## Notes

- Keep this checklist in version control
- Update before each deployment
- Use as training tool for new team members
- Share with all stakeholders
- Review lessons learned after each deployment
- [ ] `npm run type-check` → 0 errors
- [ ] `pytest backend/tests/test_e2e_flow.py` → todos pass
- [ ] No hardcoded secrets en code
- [ ] No console.log() en production

### Security
- [ ] `.env.production` tiene todas keys (no ejemplos)
- [ ] Database credentials no en git
- [ ] API keys rotados (si necesario)
- [ ] CORS configurado correcto
- [ ] Rate limiting activo

### Database
- [ ] Migrations ejecutadas: `alembic upgrade head`
- [ ] Backups configurados (daily)
- [ ] Connection pooling activo
- [ ] Indices creados

### Infrastructure
- [ ] Vercel domain verificado
- [ ] SSL certificate activo
- [ ] Firewall rules OK
- [ ] Load balancer OK
- [ ] CDN cache configurado

---

## INTEGRATION CHECKS

### Stripe
- [ ] Live API keys (sk_live, pk_live)
- [ ] Webhook endpoint verificado
- [ ] Test payment OK
- [ ] Refund test OK
- [ ] Dashboard accessible

### Mercado Libre
- [ ] Seller ID correcto
- [ ] Access token válido
- [ ] Refresh token funciona
- [ ] OAuth re-authorization working
- [ ] API rate limits OK

### WhatsApp
- [ ] WABA token válido
- [ ] Phone number ID correcto
- [ ] Webhook signing verificado
- [ ] Test message received
- [ ] Auto-responses working

### Google Calendar
- [ ] API key activo
- [ ] Calendar ID correcto
- [ ] Permissions OK
- [ ] Test event creation OK

### Shipping (DHL/FedEx)
- [ ] API keys activas
- [ ] Account numbers correctos
- [ ] Test label generation OK
- [ ] Tracking API working

### Analytics
- [ ] Database queries OK
- [ ] KPIs calculating correctly
- [ ] Dashboard responsive
- [ ] No query timeouts

### FeedIA
- [ ] Partner API key active
- [ ] Webhook endpoints configured
- [ ] Content creation requests working
- [ ] Publishing working
- [ ] Analytics feedback loop OK

---

## PERFORMANCE

### Backend
- [ ] API response time < 500ms (p95)
- [ ] Database queries < 200ms
- [ ] No memory leaks (heap size stable)
- [ ] Concurrency tested (100+ simultaneous requests)

### Frontend
- [ ] Page load < 3s (Lighthouse score > 80)
- [ ] Bundle size < 500KB
- [ ] Images optimized
- [ ] Lazy loading working

### Infrastructure
- [ ] CPU usage < 70% baseline
- [ ] Memory usage stable
- [ ] Disk space > 10% free
- [ ] Network latency OK

---

## MONITORING SETUP

### Alerts Configured
- [ ] High error rate (>5% requests failing)
- [ ] API latency spike (>1s p95)
- [ ] Database down
- [ ] Payment failures
- [ ] Webhook failures
- [ ] Disk space low (<5%)
- [ ] Memory leak detected

### Logging Active
- [ ] Structured logging (JSON format)
- [ ] Error tracking (Sentry or similar)
- [ ] Request logging
- [ ] Performance metrics
- [ ] Audit trail (payments, refunds, etc)

### Dashboards Created
- [ ] Real-time KPIs (revenue, orders, CAC, LTV)
- [ ] System health (CPU, memory, disk)
- [ ] API performance (latency, error rate)
- [ ] Business metrics (conversion rate, retention)

---

## USER TESTING

### Functional Tests
- [ ] User signup works
- [ ] Setup guide followed correctly
- [ ] Stripe checkout flow end-to-end
- [ ] Mercado Libre orders sync
- [ ] WhatsApp messages received + responded
- [ ] Shipping labels generated
- [ ] Refund process works
- [ ] Analytics dashboard loads

### Edge Cases
- [ ] High order volume (500+ orders/day)
- [ ] Concurrent checkout sessions
- [ ] Order cancellations
- [ ] Refund with missing evidence
- [ ] Expired API tokens (auto-refresh)
- [ ] Network failures (retry logic)

### User Experience
- [ ] Setup time < 30 minutes
- [ ] Dashboard intuitive
- [ ] Error messages helpful
- [ ] No 404 errors
- [ ] Mobile responsive

---

## DOCUMENTATION

- [ ] SETUP_GUIDE.md complete
- [ ] API documentation current
- [ ] Troubleshooting guide complete
- [ ] Architecture diagram updated
- [ ] Database schema documented
- [ ] Integration guide for third-party APIs

---

## DEPLOYMENT EXECUTION

### Backend Deployment
```bash
# 1. Test en staging first
vercel --prod --env production

# 2. Verify health
curl https://api.sellias.com/health

# 3. Smoke tests
bash scripts/live_test.sh

# 4. Monitor logs
vercel logs -f
```

### Frontend Deployment
```bash
# 1. Build
npm run build

# 2. Test build locally
npm run start

# 3. Deploy
vercel --prod

# 4. Verify
curl https://sellias.vercel.app
```

### Database
```bash
# 1. Backup existing database
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. Run migrations
alembic upgrade head

# 3. Verify data integrity
psql -c "SELECT COUNT(*) FROM orders;"
```

---

## POST-DEPLOYMENT

### Immediate (First Hour)
- [ ] Zero critical errors in logs
- [ ] Webhook events flowing
- [ ] Test transaction completed
- [ ] Analytics dashboard populated
- [ ] No timeout errors

### Short-term (First Day)
- [ ] Monitor error rate (< 1%)
- [ ] Check API latency (< 500ms p95)
- [ ] Verify database performance
- [ ] Confirm backups running
- [ ] Review user feedback

### Long-term (First Week)
- [ ] No unresolved errors
- [ ] Performance stable
- [ ] User retention tracking
- [ ] Cost monitoring (cloud expenses)
- [ ] Capacity planning (scaling needs)

---

## ROLLBACK PLAN

If critical issue:

```bash
# 1. Identify issue
vercel logs --error

# 2. Revert to previous version
vercel rollback

# 3. Restore database if needed
psql $DATABASE_URL < backup_YYYYMMDD_HHMMSS.sql

# 4. Notify users
Send email: "Experiencing technical difficulties..."

# 5. Fix locally
git revert <commit_hash>
git push

# 6. Re-deploy
vercel --prod
```

---

## SIGN-OFF

- [ ] Technical Lead: _________________ Date: _______
- [ ] Product Owner: _________________ Date: _______
- [ ] Infrastructure Lead: ___________ Date: _______

**DEPLOYMENT APPROVED FOR PRODUCTION**

---

## CONTACT

- **On-call**: support@sellias.com
- **Critical Issues**: emergency@sellias.com
- **Incident Channel**: #sellias-incidents (Slack)
