# Lead Progression + Auto-Workflow - FASE 3.3

## Overview
Automatic lead status progression on engagement signals + workflow triggers.

**Status Flow:**
```
new → contacted → engaged → qualified → won (or: bounced/unsubscribed/lost)
```

---

## Lead Status Transitions

### new → contacted
**Trigger:** First email sent
**Action:** `last_contacted = now()`

```
Email queued
    ↓
Processor sends via SendGrid
    ↓
Status changes: new → contacted
```

### contacted → engaged
**Trigger:** Email open OR email click
**Action:** Score +5 (open), +15 (click)

```
SendGrid webhook: email opened
    ↓
POST /api/v1/webhooks/sendgrid
    ↓
on_email_opened()
    ↓
Lead score: +5
Status: contacted → engaged
```

### engaged → qualified
**Trigger:** Lead meets threshold (score ≥ 70) OR manual status change
**Action:** Flag for sales follow-up

```
After multiple opens/clicks:
Score = 75 (threshold met)
    ↓
Status: engaged → qualified
    ↓
Sales team notified (webhook/integration)
```

### Terminal States
- **bounced**: Email hard bounce → halt all future sends
- **unsubscribed**: Explicit unsubscribe → no more emails
- **lost**: Lead went dark, manual mark (15+ days no response)
- **won**: Deal closed

---

## Engagement Scoring

| Event | Points | Status Change |
|-------|--------|----------------|
| Email sent | 0 | new → contacted |
| Email open | +5 | contacted → engaged (if ≥1 open) |
| Email click | +15 | → engaged immediately |
| Email bounce | -∞ | → bounced (halt) |
| Unsubscribe | 0 | → unsubscribed (halt) |

---

## No-Engagement Timeout

### Trigger
7+ days since last contact (open/click) = trigger no-engagement email

### Flow
```bash
# 1. Check timeout
POST /api/v1/progression/{lead_id}/no-engagement-check?days_threshold=7
→ {
    last_contacted: "2026-07-22T10:00:00",
    no_engagement_timeout_triggered: true,
    days_since_contact: 7
  }

# 2. Trigger re-engagement email (if workflow has NO_ENGAGEMENT step)
POST /api/v1/progression/{lead_id}/trigger-no-engagement?workflow_id=1
→ {
    status: "queued",
    execution_id: 1002,
    tracking_id: "task_..."
  }

# 3. Email sent immediately (or with delay if configured)
```

### No-Engagement Step Format
```json
{
  "step_number": 4,
  "trigger_type": "no_engagement",
  "delay_days": 7,
  "email_template": {
    "subject": "Last message: ROI calculator for {company}",
    "body": "Hi {lead_name},\n\nSince you haven't opened my previous messages...",
    "cta_text": "Calculate ROI",
    "cta_url": "https://example.com/roi"
  }
}
```

---

## Endpoints

### Manual Status Change (Testing)
```bash
POST /api/v1/progression/{lead_id}/status
Content-Type: application/json

{
  "new_status": "engaged"
}

Response:
{
  "lead_id": 42,
  "old_status": "contacted",
  "new_status": "engaged",
  "updated_at": "2026-07-29T16:00:00"
}
```

### Check No-Engagement
```bash
GET /api/v1/progression/{lead_id}/no-engagement-check?days_threshold=7

Response:
{
  "lead_id": 42,
  "status": "contacted",
  "last_contacted": "2026-07-22T10:00:00",
  "no_engagement_timeout_triggered": true,
  "threshold_days": 7,
  "days_since_contact": 7
}
```

### Trigger No-Engagement Email
```bash
POST /api/v1/progression/{lead_id}/trigger-no-engagement?workflow_id=1

Response:
{
  "status": "ok",
  "result": {
    "status": "queued",
    "execution_id": 1002,
    "tracking_id": "task_1002_..."
  }
}
```

### Get Lead Executions
```bash
GET /api/v1/progression/{lead_id}/workflow-executions

Response:
{
  "lead_id": 42,
  "executions": [
    {
      "id": 1001,
      "workflow_id": 1,
      "step_number": 1,
      "email_status": "opened",
      "sent_at": "2026-07-29T15:00:00",
      "opened_at": "2026-07-29T15:15:00",
      "clicked_at": null
    },
    ...
  ],
  "total": 4
}
```

---

## Testing Endpoints

### Simulate Email Open
```bash
POST /api/v1/progression/{lead_id}/simulate-open

Response:
{
  "status": "ok",
  "event": "email_opened",
  "lead_id": 42,
  "execution_id": 1001
}

Side effects:
- Lead score: +5
- Status: contacted → engaged
```

### Simulate Email Click
```bash
POST /api/v1/progression/{lead_id}/simulate-click?url=https://example.com

Response:
{
  "status": "ok",
  "event": "email_clicked",
  "lead_id": 42,
  "url": "https://example.com"
}

Side effects:
- Lead score: +15
- Status: → engaged
```

### Simulate Email Bounce
```bash
POST /api/v1/progression/{lead_id}/simulate-bounce?reason=hard_bounce

Response:
{
  "status": "ok",
  "event": "email_bounced",
  "lead_id": 42,
  "reason": "hard_bounce"
}

Side effects:
- Lead status: → bounced
- Lead score: 0
- All pending emails: halted
```

---

## Full Workflow Example

```bash
# 1. Create workflow with NO_ENGAGEMENT step
POST /api/v1/workflows
{
  "name": "Cold Outreach - SaaS",
  "steps": [
    {
      "step_number": 1,
      "trigger_type": "manual",
      "email_template": { ... }
    },
    {
      "step_number": 2,
      "trigger_type": "time_delay",
      "delay_days": 3,
      "email_template": { ... }
    },
    {
      "step_number": 3,
      "trigger_type": "no_engagement",
      "delay_days": 7,
      "email_template": {
        "subject": "Last message: ROI calculator",
        "body": "Hi {lead_name}, ..."
      }
    }
  ]
}
→ { id: 1, status: "draft" }

# 2. Create lead
POST /api/v1/leads
{ name: "John", email: "john@example.com", company: "Acme", score: 0 }
→ { id: 42, status: "new" }

# 3. Enroll in workflow
POST /api/v1/workflows/1/enroll-lead
{ lead_id: 42 }
→ { id: 1001, step_number: 1, status: "scheduled" }

# 4. Email sent (status: new → contacted)
Processor sends step 1 email
→ GET /api/v1/leads/42 { status: "contacted", score: 0 }

# 5. Lead opens email (no action after 3 days)
# Day 3 passes, step 2 scheduled email sent
→ GET /api/v1/leads/42 { status: "contacted", score: 0 }

# 6. No engagement for 7 days total
POST /api/v1/progression/42/no-engagement-check
→ { no_engagement_timeout_triggered: true, days_since_contact: 7 }

# 7. Trigger no-engagement email (step 3)
POST /api/v1/progression/42/trigger-no-engagement?workflow_id=1
→ { status: "queued", execution_id: 1003 }

# 8. No-engagement email sent immediately
→ Processor dequeues + sends

# 9. If lead opens this email
POST /api/v1/webhooks/sendgrid/test-open?email=john@example.com
→ Lead score: +5, status: engaged
→ GET /api/v1/progression/42/workflow-executions { total: 3 }
```

---

## Automatic Triggers (Future FASE 3.4)

### Currently Manual
- No-engagement timeout checks (manual POST)
- Status change triggers (manual POST)
- Workflow progression (handled by scheduler delays)

### Future Automation
- Cron job: check no-engagement timeouts hourly
- Event-driven: status changes auto-trigger next workflow steps
- Lead scoring: auto-update status based on score thresholds
- Analytics: auto-calculate lead health scores

---

## Lead Health Metrics

```
Score:     0-100 (engagement + fit)
Status:    new → contacted → engaged → qualified → won/lost
Velocity:  emails_sent, opens, clicks (per week)
Recency:   last_contacted (days ago)
Health:    composite score (0-100)
  = score * 40% + recency_score * 30% + velocity_score * 30%
```

### Health Score Example
```
Lead with:
- Score: 75 (high engagement)
- Last contacted: 1 day ago (fresh)
- 3 opens, 1 click in last 7 days (high velocity)
→ Health: 75 * 0.4 + 95 * 0.3 + 90 * 0.3 = 30 + 28.5 + 27 = 85.5
→ Status: "Hot lead" (95th percentile)
```

---

## Next Steps (FASE 3.4+)

- [ ] Cron-based no-engagement checks (hourly)
- [ ] Auto-status transitions on score thresholds
- [ ] Status-change workflow triggers
- [ ] Lead health scoring dashboard
- [ ] Bulk progression operations
- [ ] Audit trail (who changed status, when)
- [ ] Lead merging (duplicates)
- [ ] Unqualify leads (manual bulk action)

