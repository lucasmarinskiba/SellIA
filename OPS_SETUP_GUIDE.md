# Operations Setup Guide — Phase 29 Production

**Status:** Production deployed & verified  
**URL:** https://sellia-production.up.railway.app  
**Date:** 2026-08-26

---

## Task 1: Configure Sentry (Error Tracking)

**Objective:** Real-time error tracking + stack traces

**Steps:**

1. **Create Sentry Account**
   ```
   Go to: https://sentry.io/
   Sign up or login
   ```

2. **Create Project**
   ```
   Organization: [Your org]
   Project name: "SellIA Production"
   Platform: Python/FastAPI
   ```

3. **Get DSN**
   ```
   Settings → Projects → [Your project] → Client Keys (DSN)
   Copy: https://[key]@sentry.io/[project-id]
   ```

4. **Deploy to Production**
   ```
   Go to: https://railway.app/
   Project: impartial-hope
   Service: backend
   Environment tab → Add variable:
   
   Key:   SENTRY_DSN
   Value: https://[key]@sentry.io/[project-id]
   
   Key:   SENTRY_ENVIRONMENT
   Value: production
   
   Save → Redeploy
   ```

5. **Verify**
   ```bash
   # Wait 2 min for redeploy
   # Then check Sentry dashboard — should see new events
   ```

---

## Task 2: Setup Slack Alerts

**Objective:** Real-time Slack notifications for critical events

**Steps:**

1. **Create Slack Webhook**
   ```
   Go to: https://api.slack.com/messaging/webhooks
   Click: Create New App
   Select: From scratch
   App name: "SellIA Alerts"
   Workspace: [Your workspace]
   ```

2. **Enable Webhooks**
   ```
   Left sidebar: Incoming Webhooks
   Toggle: On
   Click: Add New Webhook to Workspace
   Channel: #incidents (create if needed)
   Authorize
   Copy webhook URL: https://hooks.slack.com/services/...
   ```

3. **Deploy to Production**
   ```
   Go to: https://railway.app/
   Project: impartial-hope
   Service: backend
   Environment tab → Add variable:
   
   Key:   ALERT_WEBHOOK_SLACK
   Value: https://hooks.slack.com/services/[your-webhook]
   
   Save → Redeploy
   ```

4. **Verify**
   ```bash
   # Test webhook:
   curl -X POST 'https://hooks.slack.com/services/[your-webhook]' \
     -H 'Content-Type: application/json' \
     -d '{"text":"Test alert from SellIA"}'
   
   # Should appear in #incidents channel
   ```

---

## Task 3: Configure PagerDuty On-Call

**Objective:** Page on-call engineer on critical issues

**Steps:**

1. **Create PagerDuty Account**
   ```
   Go to: https://www.pagerduty.com/
   Sign up (14-day free trial available)
   ```

2. **Create Service**
   ```
   Services → New Service
   Name: "SellIA Production"
   Escalation policy: Create new
     - Level 1: [Your name] (immediate)
     - Level 2: [Manager] (15 min)
     - Level 3: [CTO] (30 min)
   ```

3. **Create Integration**
   ```
   Service → [SellIA Production]
   Integrations → New integration
   Type: "Events API v2"
   Copy: Integration Key (looks like: xxxxx-xxxxx-xxxxx)
   ```

4. **Get Webhook URL**
   ```
   Integrations → Events API v2 Integration
   Webhook URL: https://events.pagerduty.com/v2/enqueue
   ```

5. **Deploy to Production**
   ```
   Go to: https://railway.app/
   Project: impartial-hope
   Service: backend
   Environment tab → Add variable:
   
   Key:   ALERT_WEBHOOK_PAGERDUTY
   Value: https://events.pagerduty.com/v2/enqueue
   
   Key:   PAGERDUTY_INTEGRATION_KEY
   Value: [Your integration key]
   
   Save → Redeploy
   ```

---

## Task 4: Create Alert Rules

**Objective:** Define when to page on-call

**Steps:**

1. **Critical Alerts (Page Immediately)**

   Configure in Railway → Alerts:
   ```
   Alert 1: Health check failing
   - Condition: /api/health not 200 for >3 minutes
   - Action: POST to ALERT_WEBHOOK_PAGERDUTY
   - Severity: CRITICAL
   
   Alert 2: High error rate
   - Condition: 5xx errors >5% of traffic
   - Action: POST to ALERT_WEBHOOK_PAGERDUTY
   - Severity: CRITICAL
   
   Alert 3: Slow responses
   - Condition: p95 latency >5s
   - Action: POST to ALERT_WEBHOOK_PAGERDUTY
   - Severity: CRITICAL
   ```

2. **Warning Alerts (Create Ticket)**

   Configure in Railway → Alerts:
   ```
   Alert 4: Moderate error rate
   - Condition: 4xx/5xx errors 1-5%
   - Action: POST to ALERT_WEBHOOK_SLACK (#incidents)
   - Severity: WARNING
   
   Alert 5: Slow responses warning
   - Condition: p95 latency 2-5s
   - Action: POST to ALERT_WEBHOOK_SLACK (#incidents)
   - Severity: WARNING
   
   Alert 6: ManyChat webhook failures
   - Condition: Webhook errors >1%
   - Action: POST to ALERT_WEBHOOK_SLACK (#incidents)
   - Severity: WARNING
   ```

3. **Monitor Setup Complete**
   ```
   Verify:
   - [ ] Sentry events flowing
   - [ ] Slack alerts configured
   - [ ] PagerDuty on-call setup
   - [ ] Alert rules created
   - [ ] Test alert triggered
   ```

---

## Execution Checklist

### Phase 1: Sentry Setup (10 min)
- [ ] Sentry account created
- [ ] Project created
- [ ] DSN copied
- [ ] SENTRY_DSN deployed to Railway
- [ ] Redeploy complete
- [ ] Events visible in Sentry dashboard

### Phase 2: Slack Setup (10 min)
- [ ] Slack app created
- [ ] Incoming webhook enabled
- [ ] Webhook URL copied
- [ ] ALERT_WEBHOOK_SLACK deployed to Railway
- [ ] Test webhook sent
- [ ] Test message visible in #incidents

### Phase 3: PagerDuty Setup (15 min)
- [ ] PagerDuty account created
- [ ] Service created
- [ ] Escalation policy configured
- [ ] Integration key copied
- [ ] PAGERDUTY_INTEGRATION_KEY deployed to Railway
- [ ] Webhook URL verified

### Phase 4: Alert Rules (15 min)
- [ ] Critical alerts configured (3 rules)
- [ ] Warning alerts configured (3 rules)
- [ ] All rules enabled
- [ ] Test alert triggered
- [ ] Alert routed to PagerDuty (CRITICAL) and Slack (WARNING)

**Total Time:** ~50 minutes

---

## Validation Scripts

Once setup complete, run:

```bash
# Check environment variables deployed
curl -s https://sellia-production.up.railway.app/api/health | grep -o '"status":"[^"]*"'

# Test Sentry
curl -s https://sellia-production.up.railway.app/debug/llm-test

# Check Slack webhook
curl -X POST $ALERT_WEBHOOK_SLACK \
  -H 'Content-Type: application/json' \
  -d '{"text":"Slack alert test from SellIA"}'

# Check PagerDuty
curl -X POST https://events.pagerduty.com/v2/enqueue \
  -H 'Content-Type: application/json' \
  -d '{
    "routing_key":"'$PAGERDUTY_INTEGRATION_KEY'",
    "event_action":"trigger",
    "payload":{
      "summary":"SellIA Alert Test",
      "severity":"critical",
      "source":"SellIA Production"
    }
  }'
```

---

## Next Steps

Once ops setup complete:

1. **Establish on-call rotation** in PagerDuty
2. **Share PRODUCTION_RUNBOOK.md** with team
3. **Monitor first 24 hours** for baseline metrics
4. **Tune alert thresholds** based on actual traffic
5. **Document learnings** in runbook

---

## Support

- Sentry docs: https://docs.sentry.io/
- Slack API: https://api.slack.com/
- PagerDuty docs: https://support.pagerduty.com/
- Railway docs: https://docs.railway.app/

---

**Status:** Ready for execution  
**Estimated Time:** 50 minutes  
**Prepared:** 2026-08-26
