# Email Automation Workflows API

## Overview
Secuencias automáticas de emails: cold outreach, nurture, follow-up.

**Base URL:** `/api/v1/workflows`

## Features

### 1. Workflow Engine
- Crear secuencias multi-paso
- Triggers: time-based, status-based, engagement-based
- Auto-enrollment de leads
- Template personalization con variables

### 2. Predefined Workflows
- **Cold Outreach - SaaS**: 4-email sequence para prospectos SaaS
- **Nurture Engaged**: 2-email follow-up para leads calificados

### 3. Email Tracking
- Scheduled, Sent, Delivered
- Opened, Clicked (webhook ready)
- Bounced, Unsubscribed

### 4. Templating
Variables soportadas:
- `{lead_name}` → John
- `{company}` → Acme Corp
- `{industry}` → SaaS
- `{offer}` → SellIA Platform
- `{button_url}` → CTA link
- `{cta_text}` → "Book a time"

---

## Workflow Structure

```json
{
  "id": 1,
  "name": "Cold Outreach - SaaS",
  "description": "5-email sequence",
  "industry_filter": "SaaS",
  "min_score_filter": 50,
  "status": "active",
  "steps": [
    {
      "step_number": 1,
      "trigger_type": "manual",
      "email_template": {
        "subject": "Quick question about {company}",
        "body": "Hi {lead_name}, ...",
        "cta_text": "Book a time",
        "cta_url": "https://calendly.com/sellia"
      }
    },
    {
      "step_number": 2,
      "trigger_type": "time_delay",
      "delay_days": 3,
      "email_template": { ... }
    }
  ],
  "active_leads": 42,
  "created_at": "2026-07-29T12:00:00",
  "updated_at": "2026-07-29T12:00:00"
}
```

### Trigger Types

**1. MANUAL**
- Enviado manualmente o por webhook externo
- Primer paso de secuencias

**2. TIME_DELAY**
- Enviar X días después de paso anterior
- E.g., follow-up 3 días después

**3. STATUS_CHANGE**
- Trigger cuando lead cambia status
- E.g., cuando status = "contacted", enviar email #2

**4. NO_ENGAGEMENT**
- Trigger si lead no abre/clickea en X días
- E.g., re-engagement email después de 7 días

---

## Endpoints

### 1. Create Workflow
```
POST /api/v1/workflows
Content-Type: application/json

{
  "name": "My Custom Sequence",
  "description": "B2B outreach for directors",
  "industry_filter": "SaaS",
  "min_score_filter": 60,
  "steps": [
    {
      "step_number": 1,
      "trigger_type": "manual",
      "email_template": {
        "subject": "Quick question about {company}",
        "body": "Hi {lead_name}, we help {industry} companies close deals faster...",
        "cta_text": "Learn more",
        "cta_url": "https://example.com"
      }
    }
  ]
}

Response:
{
  "id": 1,
  "name": "My Custom Sequence",
  "status": "draft",
  "active_leads": 0,
  "created_at": "2026-07-29T12:00:00",
  ...
}
```

### 2. List Workflows
```
GET /api/v1/workflows?status=active

Response:
[
  {
    "id": 1,
    "name": "Cold Outreach - SaaS",
    "status": "active",
    "active_leads": 42,
    ...
  },
  ...
]

Query Params:
- status: active|draft|paused|completed
```

### 3. Get Workflow Details
```
GET /api/v1/workflows/{workflow_id}

Response:
{
  "id": 1,
  "name": "Cold Outreach - SaaS",
  "steps": [ ... ],
  "active_leads": 42,
  ...
}
```

### 4. Update Workflow
```
PUT /api/v1/workflows/{workflow_id}
Content-Type: application/json

{
  "status": "paused",
  "steps": [ ... ]  # Optional, update steps
}

Response: { ... updated workflow ... }
```

### 5. Activate Workflow
```
POST /api/v1/workflows/{workflow_id}/activate

Response:
{
  "id": 1,
  "status": "active",
  "updated_at": "2026-07-29T13:00:00"
}
```

### 6. Pause Workflow
```
POST /api/v1/workflows/{workflow_id}/pause

Response:
{
  "id": 1,
  "status": "paused",
  "updated_at": "2026-07-29T13:00:00"
}
```

### 7. Enroll Lead in Workflow
```
POST /api/v1/workflows/{workflow_id}/enroll-lead
Content-Type: application/json

{
  "lead_id": 42
}

Response:
{
  "id": 1001,
  "workflow_id": 1,
  "lead_id": 42,
  "step_number": 1,
  "email_status": "scheduled",
  "sent_at": null,
  "opened_at": null,
  "clicked_at": null
}
```

### 8. Preview Email
```
POST /api/v1/workflows/template/preview
Content-Type: application/json

{
  "workflow_id": 1,
  "lead_id": 42
}

Response:
{
  "workflow_id": 1,
  "step": 1,
  "subject": "Quick question about Acme Corp",
  "body": "Hi John, we help SaaS companies close deals faster...",
  "cta": "Learn more"
}
```

### 9. List Workflow Executions
```
GET /api/v1/workflows/executions/list?workflow_id=1&status=sent

Response:
[
  {
    "id": 1001,
    "workflow_id": 1,
    "lead_id": 42,
    "lead_email": "john@example.com",
    "step_number": 1,
    "email_status": "sent",
    "sent_at": "2026-07-29T12:30:00",
    "opened_at": null,
    "clicked_at": null
  },
  ...
]

Query Params:
- workflow_id: Filter by workflow
- lead_id: Filter by lead
- status: scheduled|sent|delivered|opened|clicked|bounced
```

### 10. List Predefined Templates
```
GET /api/v1/workflows/templates/predefined

Response:
{
  "cold_outreach_saas": {
    "name": "Cold Outreach - SaaS",
    "description": "5-email cold sequence for SaaS prospects",
    "steps": 4
  },
  "nurture_engaged": {
    "name": "Nurture Engaged Leads",
    "description": "Weekly value emails for leads who engaged",
    "steps": 2
  }
}
```

### 11. Create from Predefined Template
```
POST /api/v1/workflows/templates/predefined/cold_outreach_saas

Response:
{
  "id": 5,
  "name": "Cold Outreach - SaaS",
  "status": "draft",
  "steps": 4,
  "active_leads": 0
}
```

---

## Predefined Workflows

### Cold Outreach - SaaS
4-step sequence usando **Efti (cold email) + Cialdini (persuasion)** frameworks:

**Step 1 (Manual):** Curiosity hook + problem statement
```
Subject: Quick question about {company}
Body: Simple intro, ask for 15-min call
```

**Step 2 (3-day delay):** Proof + value
```
Subject: Re: Quick question about {company}
Body: Mention ROI (40% faster close rates)
```

**Step 3 (5-day delay):** Social proof
```
Subject: Social proof from {industry} companies
Body: Name-drop, show playbook
```

**Step 4 (7-day delay, if no engagement):** Re-engagement + urgency
```
Subject: Last message: ROI calculator for {company}
Body: Last chance, give alternative (unsubscribe)
```

### Nurture Engaged Leads
2-step sequence para leads que ya respondieron:

**Step 1 (On status=contacted):** Value content
```
Body: 3 trends in their industry
```

**Step 2 (7-day delay):** Implementation guide
```
Body: How to implement AI-driven selling (3-step framework)
```

---

## Integration with Leads API

### Example: Full Funnel
```bash
# 1. Create lead
POST /api/v1/leads
{ name: "John", email: "john@example.com", company: "Acme", ... }
→ Response: { id: 42, score: 75 }

# 2. Load predefined workflow
POST /api/v1/workflows/templates/predefined/cold_outreach_saas
→ Response: { id: 1, status: "draft" }

# 3. Activate workflow
POST /api/v1/workflows/1/activate
→ Response: { status: "active" }

# 4. Enroll lead
POST /api/v1/workflows/1/enroll-lead
{ lead_id: 42 }
→ Response: { id: 1001, email_status: "scheduled" }

# 5. Track engagement
Monitor /api/v1/workflows/executions/list?lead_id=42
→ See opens, clicks, etc.

# 6. Update lead status
PUT /api/v1/leads/42
{ status: "contacted" }
→ Triggers next steps in nurture workflow
```

---

## Scheduling (FASE 3)
Currently: In-memory + mock status
FASE 3: Add:
- Redis queue (celery)
- SendGrid/SMTP integration
- Webhook handlers (email open tracking)
- Automatic lead progression
- Bounce handling

---

## Next Steps
- [ ] SMTP/SendGrid integration
- [ ] Redis queue + scheduler
- [ ] Webhook handlers for opens/clicks
- [ ] Auto-progression (status change → next email)
- [ ] A/B testing framework
- [ ] Bounce + unsubscribe handling
- [ ] Multi-language templates
