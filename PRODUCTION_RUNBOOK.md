# Production Runbook — Phase 29 (ManyChat + Auto-Qualification + Booking)

## Deployment Information

**Application:** SellIA (Sellia Brain)
**Phase:** 29 — Real ManyChat Integration + Auto-Qualification + Booking Rates
**Deployment Platform:** Railway
**Entry Point:** `app.main:app`
**Health Check:** `GET /api/health`

---

## Pre-Deployment Checklist

- [x] Code deployed to main (af4c1bf)
- [x] Database schema migrated (business_contexts table + patches)
- [x] All routers registered (50+ endpoints)
- [x] Debug endpoints available (tags=["debug"])
- [x] E2E test suite ready (16-point verification)
- [ ] Production URL obtained from Railway
- [ ] E2E tests run and verified
- [ ] Monitoring/alerting configured
- [ ] Error tracking (Sentry) enabled
- [ ] Logging aggregation active

---

## Critical Endpoints

**Health & Status:**
- `GET /api/health` → System health
- `GET /api/ping` → Availability check

**ManyChat Integration:**
- `POST /api/v1/businesses/webhook/manychat?token=...` → Webhook ingestion
- `GET /api/v1/businesses/{id}/channels` → List channels

**Auto-Qualification:**
- `GET /api/v1/lead-qualifier/leads?business_id=...` → View qualified leads
- `POST /debug/qualify/{conversation_id}` → Manual qualification (debug)

**Communication Angles:**
- `POST /api/v1/business-context/{id}/generate-angles` → Generate angles
- `GET /api/v1/business-context/{id}` → Retrieve context

**Booking Metrics:**
- `POST /api/v1/bookings/webhook/{business_id}?token=...` → Record booking
- `GET /api/v1/bookings/metrics?business_id=...` → Get booking rate

---

## Production Monitoring (Post-Deployment)

### Metrics to Track

**System Health:**
- API response time (p50, p95, p99)
- Error rate (4xx, 5xx)
- Database connection pool usage
- Queue depth (if async tasks)

**Feature Metrics:**
- ManyChat webhook ingestion rate (msgs/min)
- Auto-qualification success rate (%)
- Average BANT score
- Booking conversion rate (%)
- LLM API call latency

### Alerts to Configure

**Critical (Page on-call):**
- Health check failing (3+ min)
- Database connection pool exhausted
- ManyChat webhook errors (>10% of traffic)
- Booking rate <50% (indicates broken qualification)

**Warning (Create incident ticket):**
- Response time >2s (p95)
- Error rate >1%
- LLM API timeouts >5% of calls
- Qualification score anomaly

### Dashboard to Create

**Top-level overview:**
- Uptime (%)
- Error rate (%)
- Avg response time (ms)
- Requests per minute

**Feature breakdown:**
- ManyChat webhook volume
- Qualification rate (qualified vs disqualified)
- Average booking rate
- LLM call success rate

---

## Incident Response

### ManyChat Webhook Failures

**Symptoms:**
- Messages not appearing in system
- `/businesses/webhook/manychat` returning 4xx/5xx

**Debug Steps:**
1. Check Railway logs: `railway logs --deployment [id]`
2. Verify webhook token: `GET /api/v1/bookings/webhook-token?business_id=...`
3. Test manually: `POST /api/v1/businesses/webhook/manychat?token=test`
4. Check ManyChat credential validity

**Resolution:**
- Verify ManyChat API token in credentials
- Check channel webhook configuration
- Review channel creation payload
- Retry failed messages manually if needed

### Auto-Qualification Not Triggering

**Symptoms:**
- Messages ingested but no LeadQualification records
- Debug endpoint shows conversations but no qualifications

**Debug Steps:**
1. Check debug endpoint: `GET /debug/conversation-state/{business_id}`
2. Verify 2+ messages on conversation
3. Check LLM API availability (Anthropic/OpenAI)
4. Review LLM timeouts in logs

**Resolution:**
- Ensure ANTHROPIC_API_KEY or OpenAI key is set
- Check LLM call timeout (30s default)
- Manually trigger: `POST /debug/qualify/{conversation_id}`
- Check BANT scorer model availability

### Low Booking Rates

**Symptoms:**
- Many qualified leads but few bookings
- Booking rate <50%

**Debug Steps:**
1. Verify booking webhook URL configured
2. Test booking webhook: `POST /api/v1/bookings/webhook/{id}?token=...`
3. Check booking event creation: `GET /api/v1/bookings/metrics?business_id=...`
4. Verify booking tool (Calendly/cal.com) webhook setup

**Resolution:**
- Confirm booking tool webhook points to correct Railway URL
- Re-fetch webhook token if changed
- Trace booking event ingestion with debug endpoint
- Manually record test booking

---

## Deployment Procedures

### Deploy New Version

```bash
git add .
git commit -m "Phase 29: [description]"
git push origin main
# Railway auto-deploys on main push
```

### Rollback to Previous Version

```bash
git revert [commit-hash]
git push origin main
# Or direct rollback:
railway redeploy [previous-deployment-id]
```

### Emergency Stop

```bash
railway down  # Stop latest deployment
# Or from dashboard: Deployments → Stop
```

---

## Performance Targets

**API Latency:**
- Health check: <100ms
- Standard endpoints: <200ms p95
- LLM calls: <5s p95 (expected: 2-3s)

**Reliability:**
- Uptime: 99.5% minimum
- Error rate: <0.1%
- Webhook success rate: >99%

**Qualification:**
- BANT scoring latency: <3s
- Auto-qualification trigger: <10s after 2nd message
- Booking webhook ingestion: <100ms

---

## Known Limitations

1. **LLM API Dependency**
   - Qualification and angle generation require API access
   - Fallback to defaults if API unavailable
   - No local model fallback currently

2. **ManyChat API Dependency**
   - Tag subscriber and send message require ManyChat token
   - No retry logic for failed tag operations
   - Consider implementing circuit breaker

3. **Database Connection**
   - Postgres required for production (SQLite used in dev)
   - Connection pool size: 20 (configurable)
   - Recycle interval: 3600s

4. **Real-time Updates**
   - No WebSocket/streaming yet
   - Polling required for live updates
   - Consider adding server-sent events

---

## Maintenance Tasks

**Weekly:**
- Review error logs
- Check API latency trends
- Verify webhook delivery

**Monthly:**
- Audit ManyChat credentials
- Review database performance
- Clean up old debug logs

**Quarterly:**
- Analyze qualification metrics
- Review LLM API costs
- Update runbook based on learnings

---

## Contact & Escalation

**On-Call Escalation:**
1. Auto-alerts via Sentry/monitoring
2. Page on-call engineer (PagerDuty integration)
3. Critical issues: Contact platform team

**Support Resources:**
- Railway: https://railway.app/support
- ManyChat: https://manychat.com/support
- LLM provider: Anthropic/OpenAI support

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-08-26 | Initial Phase 29 runbook |

---

**Last Updated:** 2026-08-26
**Maintained By:** Platform Team
**Next Review:** 2026-09-26
