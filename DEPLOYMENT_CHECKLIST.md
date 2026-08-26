# Phase 29 Deployment Checklist

**Status:** Ready for Production Verification  
**Date:** 2026-08-26  
**Version:** af4c1bf + operational docs

---

## ✅ Pre-Deployment (Already Complete)

### Code Quality
- [x] All code committed to main
- [x] Zero production warnings
- [x] Schema migrations applied
- [x] 50+ API endpoints registered
- [x] Debug endpoints available
- [x] Transaction safety verified
- [x] Type hints strict

### Documentation
- [x] PRODUCTION_RUNBOOK.md
- [x] OBSERVABILITY_SETUP.md  
- [x] GET_PRODUCTION_URL.md

---

## 🔄 Steps to Production

### Step 1: Get Production URL
Go to https://railway.app/ → Find SellIA project → Copy backend service URL

### Step 2: Run E2E Tests
```bash
./run_e2e_tests.sh https://[your-railway-url]
# Expected: 16/16 tests pass
```

### Step 3: Configure Monitoring
```bash
./setup-on-call.sh https://[your-railway-url]
# Sets up Sentry + Slack + PagerDuty
```

### Step 4: Establish On-Call
- Configure PagerDuty escalation policy
- Set alert rules (critical: health failing >3min)
- Share PRODUCTION_RUNBOOK.md with team

---

## 📊 Monitoring

**System Health:**
- Uptime (target: 99.5%)
- Error rate (target: <0.1%)  
- Response time p95 (target: <200ms)

**Feature Metrics:**
- ManyChat webhook throughput
- Qualification success rate
- Booking conversion rate
- LLM API latency

---

## 🚨 Incident Response

**Health check fails:**
```bash
railway logs --follow
curl https://[url]/api/health
```

**ManyChat not flowing:**
- Check webhook token
- Test: POST /api/v1/businesses/webhook/manychat
- Verify ManyChat credentials

**Qualification not triggering:**
- Check LLM API (Anthropic/OpenAI)
- Test: POST /debug/qualify/{conversation_id}
- Check timeout settings

---

## 📚 Files Ready

| File | Status |
|------|--------|
| PRODUCTION_RUNBOOK.md | ✅ Complete |
| OBSERVABILITY_SETUP.md | ✅ Complete |
| monitoring-config.env | ✅ Template |
| setup-on-call.sh | ✅ Ready |
| run_e2e_tests.sh | ✅ Ready |

---

## ✨ Next Phase

Once verified in production:
1. Monitor baseline metrics (week 1)
2. Iterate on qualification thresholds  
3. Optimize LLM prompts
4. Scale to multiple business types
5. Plan Phase 30: Advanced analytics

---

**Last Updated:** 2026-08-26  
**Next Review:** 2026-09-26
