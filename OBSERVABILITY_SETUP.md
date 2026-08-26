# Observability & Monitoring Setup — Phase 29

## Overview

Production readiness requires complete observability: logging, metrics, tracing, and alerting.

---

## Logging Configuration

### Railway Native Logs

```bash
# View all logs
railway logs

# Follow live logs
railway logs --follow

# Filter by service
railway logs --service backend

# Export logs
railway logs --output json > logs.json
```

### Application Logging

**Current Configuration:**
- Log level: INFO (production), DEBUG (development)
- Format: JSON (structured logging)
- Handler: python-json-logger

**Logs Captured:**
- API requests (method, path, status, latency)
- Database operations (schema patches, queries)
- LLM calls (provider, tokens, latency)
- ManyChat API calls (success/failure)
- Errors (stack traces, context)

**Log Retention:**
- Railway default: 30 days
- Configure longer retention if needed

---

## Metrics to Expose

### Add Prometheus Metrics

Install `prometheus-client`:
```bash
pip install prometheus-client
```

Add to `app.main.py`:
```python
from prometheus_client import Counter, Histogram, generate_latest
import time

# Define metrics
webhook_counter = Counter('manychat_webhooks_total', 'Total ManyChat webhooks')
qualification_counter = Counter('qualifications_total', 'Total qualifications', ['status'])
booking_counter = Counter('bookings_total', 'Total bookings')
api_latency = Histogram('api_latency_seconds', 'API latency')

# Expose metrics endpoint
@app.get("/metrics", tags=["monitoring"])
async def metrics():
    return generate_latest()
```

### Metrics Endpoint

```bash
# Get all metrics
curl https://[production-url]/metrics
```

---

## Error Tracking (Sentry)

### Setup

1. Create Sentry account: https://sentry.io/
2. Create project for SellIA
3. Install SDK:
   ```bash
   pip install sentry-sdk[fastapi]
   ```

4. Configure in `app.main.py`:
   ```python
   import sentry_sdk
   from sentry_sdk.integrations.fastapi import FastApiIntegration

   sentry_sdk.init(
       dsn=os.getenv("SENTRY_DSN"),
       integrations=[FastApiIntegration()],
       traces_sample_rate=0.1,  # 10% of transactions
       environment=os.getenv("ENVIRONMENT", "production"),
   )
   ```

5. Set `SENTRY_DSN` in Railway environment

### Sentry Dashboard

- Real-time error alerting
- Stack trace analysis
- Release tracking
- Performance monitoring

---

## Alerting Rules

### Configure via Railway

1. Go to Railway dashboard → Project → Alerts
2. Set up webhooks to:
   - PagerDuty (on-call)
   - Slack (incident channel)
   - Email (critical issues)

### Alert Rules

**Critical:**
```
- Health check failing for 3+ minutes
- Error rate > 5%
- Response time p95 > 5s
```

**Warning:**
```
- Error rate > 1%
- Response time p95 > 2s
- ManyChat webhook failures > 1%
```

---

## Dashboard Setup

### Grafana (Recommended)

1. Spin up Grafana on Railway
2. Connect to Prometheus
3. Create dashboards:

**Dashboard 1: System Health**
- Uptime (%)
- Error rate (%)
- Response time (p50, p95, p99)
- Active requests

**Dashboard 2: Feature Metrics**
- ManyChat webhook volume
- Qualification rate
- Booking conversion rate
- LLM API latency

**Dashboard 3: Database Health**
- Connection pool usage
- Query latency
- Slow queries
- Transaction rate

---

## Performance Baselines

### Target SLIs

**Availability:**
- 99.5% uptime
- <5 min incident recovery

**Latency:**
- Health check: <100ms
- API endpoints: <200ms p95
- LLM calls: <5s p95

**Quality:**
- Error rate: <0.1%
- Webhook success: >99%
- Qualification accuracy: >90%

### Baseline Measurements

**Before Production Release:**
```bash
# Load test
k6 run load_test.js

# Check baselines
curl /metrics
```

---

## Incident Response SOP

### Alert Received

1. **Acknowledge alert** (PagerDuty/Slack)
2. **Check dashboard** (Is it real? Widespread or localized?)
3. **Review logs** (`railway logs --follow`)
4. **Check status page** (Are dependent services down?)

### Investigation

1. **Health checks**
   ```bash
   curl /api/health
   curl /api/ping
   ```

2. **Feature-specific checks**
   - ManyChat: `GET /debug/conversation-state/{business_id}`
   - Qualification: `POST /debug/qualify/{conversation_id}`
   - Booking: `GET /api/v1/bookings/metrics`

3. **Database checks**
   ```bash
   railway connect  # Connect to Postgres
   SELECT count(*) FROM conversations;
   SELECT count(*) FROM lead_qualifications;
   ```

### Resolution

1. **Apply fix** (code change → push → auto-deploy)
2. **Verify resolution** (recheck dashboards)
3. **Document** (add to runbook)
4. **Postmortem** (if critical)

---

## Maintenance Checklist

**Daily:**
- [ ] Check uptime dashboard
- [ ] Review critical errors
- [ ] Verify ManyChat webhooks flowing

**Weekly:**
- [ ] Review SLI trends
- [ ] Check database performance
- [ ] Analyze qualification metrics

**Monthly:**
- [ ] Update runbook
- [ ] Review cost vs. performance
- [ ] Audit access logs

**Quarterly:**
- [ ] Full postmortem on incidents
- [ ] Capacity planning
- [ ] Update documentation

---

## Tools & Services

**Required:**
- Railway (deployment)
- Sentry (error tracking)
- Prometheus (metrics)

**Recommended:**
- Grafana (dashboards)
- PagerDuty (on-call)
- Datadog (APM)

**Cost Estimate:**
- Railway: $100-500/mo (compute)
- Sentry: Free-$500/mo
- Grafana: $50-200/mo
- PagerDuty: $50-200/mo

---

## Getting Started

1. **Configure Sentry:**
   ```bash
   SENTRY_DSN=https://[key]@sentry.io/[project]
   ```

2. **Deploy metrics endpoint:**
   - Add Prometheus integration
   - Expose `/metrics`

3. **Set up alerting:**
   - Create alert rules
   - Configure webhooks to Slack/PagerDuty

4. **Create dashboards:**
   - Grafana or simple HTML

5. **Monitor first week:**
   - Establish baselines
   - Tune alert thresholds
   - Document learnings

---

**Version:** 1.0
**Date:** 2026-08-26
**Maintained By:** Platform Team
