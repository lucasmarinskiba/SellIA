# SellIA Production Deployment - Quick Reference Card

Print this page and keep it handy during deployment!

---

## 🚀 45-Minute Deployment Timeline

```
T-5:  Generate credentials    python3 scripts/generate-credentials.py
T-0:  Validate environment    python3 scripts/validate-env.py
T+5:  Deploy backend          fly deploy (automated, 5 min)
T+10: Deploy frontend         vercel --prod (automated, 5 min)
T+20: Run E2E tests           npm run test:e2e (15 min)
T+35: Health checks           ./scripts/health-check.sh (10 min)
T+45: 🎉 LIVE IN PRODUCTION  
```

---

## 📝 Pre-Deployment Checklist

- [ ] DNS pointing to production
- [ ] .env.production created with all 45 variables
- [ ] Database provisioned & migrations run
- [ ] Redis cache provisioned
- [ ] Stripe live API key added (sk_live_...)
- [ ] SendGrid email configured
- [ ] Sentry error tracking enabled
- [ ] GitHub secrets configured
- [ ] Team on standby

---

## 🔧 Critical Commands

### Deployment
```bash
# One-command deploy to production
./scripts/deploy-all.sh all

# Or deploy just backend/frontend
./scripts/deploy-all.sh backend
./scripts/deploy-all.sh frontend
```

### Verification
```bash
# Health check (single run)
./scripts/health-check.sh 0

# Continuous monitoring (every 5 min)
./scripts/health-check.sh 300

# API test
curl https://api.sellia.app/healthz

# Frontend test
curl https://selldia.app
```

### Database
```bash
# Connect to production database
psql $DATABASE_URL

# Run migrations
cd backend-mvp && alembic upgrade head

# Check recent transactions
SELECT * FROM payments ORDER BY created_at DESC LIMIT 5;
```

### Backend
```bash
# Deploy to Fly.io
cd backend-mvp && fly deploy

# View logs
fly logs -a sellia-api

# Check status
fly status
```

### Frontend
```bash
# Deploy to Vercel
vercel --prod --yes

# View deployments
vercel list
```

---

## 🚨 Rollback (Emergency Only)

### Quick Rollback (< 5 min)
```bash
# Backend
fly releases -a sellia-api
fly releases rollback <VERSION> -a sellia-api

# Frontend
vercel rollback <DEPLOYMENT>
```

### Full Rollback (Database affected)
```bash
# 1. Stop application
fly apps stop sellia-api

# 2. Restore database from backup
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier sellia-db-recovery \
  --db-snapshot-identifier sellia-backup-latest

# 3. Update DB URL in secrets
fly secrets set DATABASE_URL='...'

# 4. Restart
fly apps open sellia-api
```

---

## ⚠️ Common Issues & Fixes

| Issue | Fix |
|-------|-----|
| API returning 502 | `fly restart` |
| High latency | Check DB connections: `SELECT COUNT(*) FROM pg_stat_activity;` |
| Payment failures | Verify Stripe webhook secret in env vars |
| Email not sending | Check SendGrid API key and verify sender email |
| Frontend not connecting | Check CORS settings and `NEXT_PUBLIC_API_URL` |
| Database full | Check disk space: `SELECT pg_database_size(current_database());` |
| Memory leak | Check app logs: `fly logs -a sellia-api \| grep -i memory` |

---

## 📊 Monitoring Dashboards

- **Fly.io:** https://fly.io/apps/sellia-api
- **Vercel:** https://vercel.com/projects/selldia
- **Sentry:** https://sentry.io/organizations/selldia/issues/
- **Datadog:** https://app.datadoghq.com/dashboards
- **GitHub:** https://github.com/[org]/[repo]/deployments

---

## 📞 Escalation Contacts

| Role | Contact | Availability |
|------|---------|--------------|
| On-Call Engineer | Slack @oncall | 24/7 |
| DevOps Lead | [Email] | Business hours |
| CEO/CTO | [Email] | Business hours |
| Support | support@selldia.app | 24/7 |

---

## ✅ Success Indicators

After deployment, you should see:

✅ API responding in < 200ms  
✅ Frontend loading < 3 seconds  
✅ E2E tests passing (5/5)  
✅ First payment processed  
✅ Confirmation email received  
✅ Zero critical errors in Sentry  
✅ Team celebrating 🎉  

---

## 🔐 Security Checklist

- [ ] HTTPS enabled on both frontend & backend
- [ ] DEBUG=false in production
- [ ] STRIPE_API_KEY starts with sk_live_
- [ ] .env.production in .gitignore
- [ ] Database backups enabled
- [ ] Rate limiting enabled
- [ ] CORS configured for selldia.app only
- [ ] Session cookies secure (HttpOnly, SameSite=Strict)
- [ ] No API keys in code
- [ ] Monitoring alerting configured

---

## 📈 Expected Performance

| Metric | Target | Yellow | Red |
|--------|--------|--------|-----|
| API Latency (p50) | < 100ms | 100-200ms | > 200ms |
| API Latency (p99) | < 500ms | 500-1000ms | > 1000ms |
| Error Rate | < 0.1% | 0.1-1% | > 1% |
| Payment Success | > 99% | 95-99% | < 95% |
| Frontend Load | < 3s | 3-5s | > 5s |
| Uptime | 100% | 99.9-100% | < 99.9% |

---

## 💡 Pro Tips

1. **Deploy on a weekday morning** - Team is available, support awake
2. **Have backups ready** - Test restore procedure before going live
3. **Monitor closely first hour** - Catch issues before they scale
4. **Keep rollback plan handy** - Know how to revert in < 5 minutes
5. **Communicate status** - Post updates every 15 minutes first hour
6. **Document everything** - Note any issues for post-mortem
7. **Celebrate success** - You made it live! 🎉

---

## 📋 Launch Day Timeline

```
08:00 - Final checks (15 min)
08:15 - Deploy backend (5 min)
08:20 - Deploy frontend (5 min)
08:25 - Run E2E tests (15 min)
08:40 - Health checks (10 min)
08:50 - Announce in Slack
09:00 - Monitor closely (1 hour)
10:00 - First metrics review
10:30 - Celebrate success! 🎉
```

---

## 🎯 Launch Criteria

**GO** if all boxes checked:
- [ ] All env vars validated
- [ ] Database migrations run successfully
- [ ] Backend health check passing
- [ ] Frontend loading
- [ ] E2E tests passing
- [ ] Monitoring alert test passed
- [ ] Rollback procedure tested
- [ ] Team confident

**NO-GO** if any of:
- ❌ E2E tests failing
- ❌ API latency > 1000ms
- ❌ Payment test failed
- ❌ Error rate > 1%
- ❌ Team not ready

---

## 🆘 When Things Go Wrong

**API Down (502 error):**
1. Check logs: `fly logs -a sellia-api | grep error`
2. Restart: `fly restart`
3. Still down? Rollback: `fly releases rollback <VERSION>`

**Database Down:**
1. Check connection: `psql $DATABASE_URL -c "SELECT 1;"`
2. Check disk: `SELECT pg_database_size(current_database());`
3. Restart DB: AWS console
4. Still down? Restore from backup

**Payment Failing:**
1. Check Stripe webhook: https://dashboard.stripe.com/webhooks
2. Test webhook: Send test event
3. Check logs for webhook errors
4. Verify API key: `fly secrets list | grep STRIPE`

**Email Not Sending:**
1. Check SendGrid: https://app.sendgrid.com
2. Verify sender email
3. Check API key: `fly secrets list | grep SENDGRID`
4. Check logs for errors

---

## 📊 Key Metrics to Track

Track these for first week:

- **Error rate:** Target < 0.1%
- **API latency p50:** Target < 100ms
- **API latency p99:** Target < 500ms
- **Payment success:** Target > 99%
- **Email delivery:** Target > 98%
- **Uptime:** Target 100%
- **Customer signups:** Track daily
- **Support tickets:** Monitor closely

---

## 🔗 Important Links

**Deployment:**
- DEPLOYMENT.md (full guide)
- DEPLOYMENT_GUIDE.md (quick start)
- LAUNCH_CHECKLIST.md (verification)

**Hosting Dashboards:**
- Fly.io: https://fly.io/apps/sellia-api
- Vercel: https://vercel.com/dashboard
- GitHub: https://github.com/[org]/[repo]

**Monitoring:**
- Sentry: https://sentry.io
- Datadog: https://app.datadoghq.com
- CloudWatch: https://console.aws.amazon.com/cloudwatch

**Payments:**
- Stripe: https://dashboard.stripe.com
- SendGrid: https://app.sendgrid.com

---

## ✨ Final Checklist

Before pressing deploy:

- [ ] I've read the DEPLOYMENT_GUIDE.md
- [ ] I have all credentials ready
- [ ] Database is provisioned
- [ ] Redis is running
- [ ] Stripe webhook configured
- [ ] SendGrid email verified
- [ ] All environment variables validated
- [ ] Team is on standby
- [ ] I know how to rollback
- [ ] I'm ready to go live 🚀

---

**Print this card. Keep it handy. Launch with confidence.**

🚀 **SellIA to production. 45 minutes. Go!**
