# Email Delivery + Persistence API - FASE 3 STEP 1

## Overview
Real email delivery + PostgreSQL persistence + webhook tracking.

**Components:**
- SendGrid/SMTP email sender
- SQLAlchemy ORM + async database
- Webhook handlers for opens/clicks/bounces
- Lead scoring updates on engagement

---

## Email Sender Service

### Initialization
```python
from app.core.email_sender import get_email_sender, get_email_scheduler

# Auto-detect from env: SENDGRID_API_KEY
sender = get_email_sender("sendgrid")  # or "smtp", "mock"
scheduler = get_email_scheduler("sendgrid")
```

### Configuration

**SendGrid (Production)**
```bash
export SENDGRID_API_KEY="SG.xxxxxxxxxxxxx"
```

**SMTP (Self-hosted)**
```bash
export SMTP_HOST="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_USER="your-email@gmail.com"
export SMTP_PASSWORD="your-app-password"
```

**Mock (Testing)**
```bash
# No env vars needed - defaults to mock
```

### Send Email
```python
await sender.send_email(
    to="lead@example.com",
    subject="Quick question about {company}",
    body="<html>...personalized content...</html>",
    from_email="noreply@sellia.io",
    from_name="SellIA",
    tracking_id="wf_42"  # Links to workflow execution
)

Response:
{
  "status": "sent",
  "provider": "sendgrid",
  "timestamp": "2026-07-29T15:00:00",
  "tracking_id": "wf_42"
}
```

### Schedule Email
```python
await scheduler.schedule_workflow_email(
    workflow_execution_id=1001,
    lead_email="lead@example.com",
    subject="Follow-up",
    body="<html>...",
    send_at=None  # Send immediately, or datetime for delayed
)

Response:
{
  "workflow_execution_id": 1001,
  "status": "sent",
  "sent_at": "2026-07-29T15:00:00"
}
```

---

## Database Schema

### Leads
```sql
CREATE TABLE leads (
  id INT PRIMARY KEY,
  name VARCHAR(255),
  email VARCHAR(255) UNIQUE,
  company VARCHAR(255),
  score FLOAT,
  status VARCHAR(50),  -- new, contacted, engaged, qualified, won, lost
  last_contacted DATETIME,
  created_at DATETIME,
  updated_at DATETIME
);
```

### WorkflowExecutions (Email Tracking)
```sql
CREATE TABLE workflow_executions (
  id INT PRIMARY KEY,
  workflow_id INT,
  lead_id INT,
  lead_email VARCHAR(255),
  step_number INT,
  email_status VARCHAR(50),  -- scheduled, sent, delivered, opened, clicked, bounced
  tracking_id VARCHAR(100) UNIQUE,
  sent_at DATETIME,
  opened_at DATETIME,
  opened_count INT,
  clicked_at DATETIME,
  clicked_count INT,
  bounced_at DATETIME,
  created_at DATETIME
);
```

### EmailLogs (Audit Trail)
```sql
CREATE TABLE email_logs (
  id INT PRIMARY KEY,
  tracking_id VARCHAR(100),
  lead_email VARCHAR(255),
  provider VARCHAR(50),  -- sendgrid, smtp
  status VARCHAR(50),
  sent_at DATETIME,
  opened_at DATETIME,
  clicked_at DATETIME,
  created_at DATETIME
);
```

---

## Webhook Handlers

### SendGrid Webhook

**Setup:**
1. In SendGrid Dashboard: Settings → Mail Send Settings → Event Notification
2. Set HTTP POST URL: `https://api.sellia.io/api/v1/webhooks/sendgrid`
3. Check events: Delivered, Open, Click, Bounce, Unsubscribe
4. Verify webhook signing (optional but recommended)

**Event Payload:**
```json
[
  {
    "email": "lead@example.com",
    "event": "open",
    "timestamp": 1690733000,
    "sg_message_id": "...",
    "sg_event_id": "..."
  },
  {
    "email": "lead@example.com",
    "event": "click",
    "timestamp": 1690733015,
    "url": "https://calendly.com/sellia",
    "sg_message_id": "..."
  },
  {
    "email": "lead@example.com",
    "event": "bounce",
    "timestamp": 1690733030,
    "reason": "hard_bounce",
    "sg_message_id": "..."
  }
]
```

**Endpoint:**
```
POST /api/v1/webhooks/sendgrid
Content-Type: application/json

Payload: [{ email, event, timestamp, ... }]

Response: { "status": "ok", "events_processed": 3 }
```

---

## Engagement Scoring

### Score Updates on Events

**Email Open: +5 points**
- Lead showed interest
- Updates: `email_status = "opened"`, `last_contacted = now()`

**Email Click: +15 points**
- Strong intent signal
- Updates: `status = "engaged"`, `email_status = "clicked"`

**Email Bounce: -∞ (set to 0)**
- Invalid email
- Updates: `status = "bounced"`, halt future sends

**Email Unsubscribe: freeze (no more emails)**
- Updates: `status = "unsubscribed"`

---

## Integration Example

### Full Workflow: Create → Send → Track

```bash
# 1. Create lead
POST /api/v1/leads
{
  "name": "John Doe",
  "email": "john@example.com",
  "company": "Acme Corp",
  "score": 0
}
→ Response: { id: 42, score: 0 }

# 2. Load workflow + activate
POST /api/v1/workflows/templates/predefined/cold_outreach_saas
→ Response: { id: 1, status: "draft" }

POST /api/v1/workflows/1/activate
→ Response: { status: "active" }

# 3. Enroll lead (triggers step 1 email send)
POST /api/v1/workflows/1/enroll-lead
{ "lead_id": 42 }
→ Response: {
    id: 1001,
    workflow_id: 1,
    lead_id: 42,
    step_number: 1,
    email_status: "scheduled"
  }

# 4. Email sends via SendGrid
EmailSender.send_email(
  to: "john@example.com",
  subject: "Quick question about Acme Corp",
  body: "<html>Hi John, ...</html>",
  tracking_id: "wf_1001"
)
→ Response: { status: "sent", provider: "sendgrid" }

# 5. SendGrid tracks events
[Webhook] Email opened at 2026-07-29 15:05:00
→ PUT workflows/executions/1001 { opened_at: "...", score_change: +5 }

[Webhook] Email clicked link at 2026-07-29 15:10:00
→ PUT workflows/executions/1001 { clicked_at: "...", status: "clicked" }
→ PUT leads/42 { status: "engaged", score: 20 }

# 6. Query lead status
GET /api/v1/leads/42
→ Response: {
    id: 42,
    name: "John Doe",
    email: "john@example.com",
    status: "engaged",
    score: 20,
    last_contacted: "2026-07-29T15:10:00"
  }
```

---

## Lead Status Flow

```
new (score: 0)
    ↓
contacted (reached out, score: 0-30)
    ↓
engaged (opened/clicked email, score: 30-70)
    ↓
qualified (scheduled call, score: 70+)
    ↓
won (closed deal) OR lost (no engagement)
    ↓
bounced (invalid email) OR unsubscribed
```

---

## Database Setup

### Local PostgreSQL (Dev)
```bash
# Start PostgreSQL
brew install postgresql
brew services start postgresql

# Create database
createdb sellia

# Set env
export DATABASE_URL="postgresql+asyncpg://postgres:@localhost:5432/sellia"
```

### Heroku PostgreSQL (Prod)
```bash
heroku addons:create heroku-postgresql:standard-0
heroku config:get DATABASE_URL
→ PostgreSQL URI auto-set in env
```

### SQLite (Testing)
```bash
# Falls back automatically if DATABASE_URL not set
export DATABASE_URL="sqlite+aiosqlite:///./test.db"
```

### Initialize Tables
```python
# Runs on startup (app lifespan)
from app.db import init_db
await init_db()
# Creates all tables + indexes
```

---

## Monitoring

### Email Delivery Metrics
```
GET /api/v1/analytics/email
→ {
    total_sent: 1250,
    delivered: 1100,
    delivery_rate: 0.88,
    opened: 450,
    open_rate: 0.41,
    clicked: 120,
    click_rate: 0.10,
    bounced: 50,
    bounce_rate: 0.04,
    unsubscribed: 20
  }
```

### Lead Engagement
```
GET /api/v1/analytics/leads?status=engaged
→ {
    total: 450,
    avg_score: 65,
    high_intent: 120,
    contacted_last_7d: 340,
    converted_rate: 0.18
  }
```

---

## Error Handling

### Common Issues

**SendGrid API Error (401)**
- Check: `SENDGRID_API_KEY` env var
- Regenerate key in SendGrid dashboard

**Database Connection Timeout**
- Check: PostgreSQL running
- Check: DATABASE_URL format correct
- Fallback: SQLite for testing

**Webhook Signature Verification Failed**
- SendGrid signing key: Settings → Mail Send Settings → Verify Webhook Signature
- Implement in email_webhooks.py (optional for FASE 3.1)

---

## Testing

### Manual Email Send (Mock)
```bash
POST /api/v1/sequences/cold-email
{
  "lead": {
    "name": "John",
    "email": "john@example.com",
    "company": "Acme",
    "title": "CEO",
    "pain_point": "Sales process too slow",
    "industry": "SaaS"
  },
  "offer": "SellIA Platform",
  "sender_email": "noreply@sellia.io"
}
→ Response: { sequence_id, emails: [...] }
```

### Test Webhook Events (Simulated)
```bash
# Simulate open
POST /api/v1/webhooks/sendgrid/test-open?email=john@example.com

# Simulate click
POST /api/v1/webhooks/sendgrid/test-click?email=john@example.com&url=https://calendly.com

# Simulate bounce
POST /api/v1/webhooks/sendgrid/test-bounce?email=john@example.com&reason=hard_bounce
```

---

## Next Steps (FASE 3.2+)

- [ ] Redis queue for email scheduling
- [ ] Celery tasks for delayed/batched sends
- [ ] A/B testing framework (subject line, body variants)
- [ ] Bounce management + auto-cleanup
- [ ] Reply parsing (v2 - read responses)
- [ ] Multi-language templates
- [ ] Webhook signature verification (security)
- [ ] Rate limiting (SendGrid rate limits)

---

## Architecture Summary

```
Lead → Workflow Enrollment → Email Scheduled
                                    ↓
                        (SendGrid/SMTP sends)
                                    ↓
                        Database: email_status = "sent"
                                    ↓
                    (User opens/clicks in client)
                                    ↓
                    (SendGrid webhook fires)
                                    ↓
                    POST /api/v1/webhooks/sendgrid
                                    ↓
                    Update email_status + lead score
                                    ↓
                    Lead status transitions
                                    ↓
                    Next workflow step (if no-engagement trigger met)
```
