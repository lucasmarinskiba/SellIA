# Lead Sources API - Prospecting

## Overview
Múltiples canales para generar leads: LinkedIn, website forms, manual, referrals.

**Base URL:** `/api/v1/lead-sources`

## Features

### 1. Lead Source Types
- **LinkedIn**: Scraper + lead enrichment (MOCK ready for real API)
- **Website**: Form integrations, auto-enrollment
- **Manual**: CSV import, CLI, API
- **Referral**: Partner referrals, customer referrals
- **Email**: Inbox parsing (v2)
- **Cold Outreach**: Reverse leads from email responses

### 2. Predefined Sources
- **LinkedIn - SaaS Sales Leaders**: VP Sales, Sales Directors
- **LinkedIn - Tech Founders**: Founders, CTOs, startup founders

### 3. Auto-Workflow Integration
Cada lead source puede auto-enrollar leads en workflow:
```
Lead generado → Auto-enroll en workflow → Email sequence comienza
```

### 4. Analytics
- Leads generated por source
- This month / this week
- Conversion rate by source
- Average score by source

---

## Lead Source Structure

```json
{
  "id": 1,
  "name": "LinkedIn - SaaS Sales Leaders",
  "description": "Busca VP Sales en SaaS companies",
  "source_type": "linkedin",
  "status": "active",
  "auto_workflow_id": 1,
  "industry_filter": "SaaS",
  "config": {
    "search_keywords": ["VP Sales", "Sales Director"],
    "search_title": ["VP Sales", "Director of Sales"],
    "company_keywords": ["SaaS", "Software"],
    "min_connections": 300,
    "filter_country": "US"
  },
  "leads_generated": 42,
  "created_at": "2026-07-29T12:00:00",
  "updated_at": "2026-07-29T12:00:00",
  "last_fetch": "2026-07-29T14:30:00"
}
```

---

## Endpoints

### 1. Create Lead Source
```
POST /api/v1/lead-sources
Content-Type: application/json

{
  "name": "LinkedIn - Enterprise CTOs",
  "description": "Busca CTOs en empresas enterprise",
  "source_type": "linkedin",
  "auto_workflow_id": 2,
  "config": {
    "search_keywords": ["CTO", "Chief Technology Officer", "VP Engineering"],
    "search_title": ["CTO", "VP Engineering"],
    "company_keywords": ["Enterprise", "Fortune 500"],
    "min_connections": 500,
    "filter_country": "US"
  }
}

Response:
{
  "id": 2,
  "name": "LinkedIn - Enterprise CTOs",
  "source_type": "linkedin",
  "status": "active",
  "leads_generated": 0,
  ...
}
```

### 2. List Lead Sources
```
GET /api/v1/lead-sources?status=active

Response:
[
  {
    "id": 1,
    "name": "LinkedIn - SaaS Sales Leaders",
    "source_type": "linkedin",
    "status": "active",
    "leads_generated": 42,
    ...
  },
  ...
]

Query Params:
- status: active|paused|inactive
```

### 3. Get Lead Source Details
```
GET /api/v1/lead-sources/{source_id}

Response:
{
  "id": 1,
  "name": "LinkedIn - SaaS Sales Leaders",
  "config": { ... },
  "leads_generated": 42,
  ...
}
```

### 4. Update Lead Source
```
PUT /api/v1/lead-sources/{source_id}
Content-Type: application/json

{
  "status": "paused",
  "auto_workflow_id": 3
}

Response: { ... updated source ... }
```

### 5. Activate Lead Source
```
POST /api/v1/lead-sources/{source_id}/activate

Response:
{
  "id": 1,
  "status": "active",
  "updated_at": "2026-07-29T15:00:00"
}
```

### 6. Pause Lead Source
```
POST /api/v1/lead-sources/{source_id}/pause

Response:
{
  "id": 1,
  "status": "paused",
  "updated_at": "2026-07-29T15:00:00"
}
```

### 7. Fetch Leads from Source
```
POST /api/v1/lead-sources/{source_id}/fetch-leads

Response:
{
  "source_id": 1,
  "source_type": "linkedin",
  "leads_found": 3,
  "leads": [
    {
      "name": "Sarah Johnson",
      "email": "sarah@techcorp.com",
      "company": "TechCorp",
      "job_title": "VP Sales",
      "notes": "LinkedIn profile: https://... Connections: 750"
    },
    ...
  ],
  "message": "Found 3 leads. Enroll in workflow to start outreach."
}
```

### 8. Website Form Submission
```
POST /api/v1/lead-sources/website/submit-form
Content-Type: application/json

{
  "name": "John Doe",
  "email": "john@example.com",
  "company": "Acme Corp",
  "message": "Interested in learning more about SellIA",
  "form_source": "https://example.com/sales-contact"
}

Response:
{
  "status": "received",
  "email": "john@example.com",
  "message": "Lead received. Will be enrolled in nurture workflow.",
  "timestamp": "2026-07-29T15:05:00"
}
```

### 9. Referral Submission
```
POST /api/v1/lead-sources/referral/submit?referrer_name=Jane&referrer_email=jane@example.com&referred_name=John&referred_email=john@example.com&referred_company=TechCorp

Response:
{
  "status": "received",
  "referred_email": "john@example.com",
  "referrer": "jane@example.com",
  "message": "Referral recorded. Lead will be marked as high priority.",
  "timestamp": "2026-07-29T15:05:00"
}
```

### 10. Lead Source Analytics
```
GET /api/v1/lead-sources/{source_id}/analytics

Response:
{
  "source_id": 1,
  "source_name": "LinkedIn - SaaS Sales Leaders",
  "source_type": "linkedin",
  "total_leads": 42,
  "this_month": 42,
  "this_week": 10,
  "avg_score": 65.0,
  "converted_count": 8,
  "conversion_rate": 0.20
}
```

### 11. List Predefined Templates
```
GET /api/v1/lead-sources/templates/predefined

Response:
{
  "linkedin_saas_sales_leaders": {
    "name": "LinkedIn - SaaS Sales Leaders",
    "description": "Busca VP Sales + Sales Directors en SaaS",
    "source_type": "linkedin"
  },
  "linkedin_tech_founders": {
    "name": "LinkedIn - Tech Founders",
    "description": "Busca Founders y CTOs de startups tech",
    "source_type": "linkedin"
  }
}
```

### 12. Create from Predefined Template
```
POST /api/v1/lead-sources/templates/predefined/linkedin_saas_sales_leaders

Response:
{
  "id": 1,
  "name": "LinkedIn - SaaS Sales Leaders",
  "source_type": "linkedin",
  "status": "active",
  "leads_generated": 0,
  ...
}
```

---

## Predefined Sources

### LinkedIn - SaaS Sales Leaders
```json
{
  "search_keywords": ["VP Sales", "Sales Director", "Sales Manager"],
  "search_title": ["VP Sales", "Sales Director", "Director of Sales"],
  "company_keywords": ["SaaS", "Software", "Tech"],
  "min_connections": 300,
  "filter_country": "US"
}
```
👥 Target: VP Sales + Sales Directors en SaaS companies
📍 USA focused
🔗 Min 300 LinkedIn connections

### LinkedIn - Tech Founders
```json
{
  "search_keywords": ["Founder", "CTO", "Chief Technology Officer"],
  "search_title": ["Founder", "Co-Founder", "CTO"],
  "company_keywords": ["Startup", "Tech", "AI"],
  "min_connections": 200,
  "filter_country": null
}
```
👥 Target: Founders + CTOs en startups tech
🌍 Global
🔗 Min 200 LinkedIn connections

---

## Full Funnel Example

```bash
# 1. Create LinkedIn source
POST /api/v1/lead-sources
{
  "name": "LinkedIn - SaaS Sales Leaders",
  "source_type": "linkedin",
  "auto_workflow_id": 1,  # Link to Cold Outreach workflow
  "config": { ... }
}
→ Response: { id: 1 }

# 2. Activate source
POST /api/v1/lead-sources/1/activate

# 3. Fetch leads from LinkedIn
POST /api/v1/lead-sources/1/fetch-leads
→ Response: {
    leads: [
      { name: "Sarah Johnson", email: "sarah@techcorp.com", ... },
      { name: "Mike Chen", email: "mike@startupia.com", ... },
      ...
    ]
  }

# 4. Create leads via Leads API
POST /api/v1/leads (for each LinkedIn result)
{ name: "Sarah Johnson", email: "sarah@techcorp.com", ... }
→ Response: { id: 42, score: 75 }

# 5. Auto-enroll in workflow
POST /api/v1/workflows/1/enroll-lead
{ lead_id: 42 }
→ Email sequence starts automatically

# 6. Track analytics
GET /api/v1/lead-sources/1/analytics
→ See: leads generated, conversion rate, avg score
```

---

## LinkedIn Integration (Current vs v2)

### Current (MOCK - Ready for Real)
- ✅ Structure defined
- ✅ Config schema ready
- ✅ Mock results for testing
- ✅ Lead conversion pipeline
- ❌ Real LinkedIn API (needs authentication, tokens)

### v2 (Real LinkedIn API)
Required:
1. LinkedIn OAuth authentication
2. LinkedIn Recruiter API key
3. Email enrichment service (RocketReach, Hunter, etc.)
4. Rate limiting + retry logic
5. Webhook for profile updates

### To Enable Real LinkedIn:
1. Get LinkedIn API credentials
2. Implement LinkedIn OAuth flow
3. Replace `mock_linkedin_search()` with real API call
4. Add email enrichment service
5. Handle rate limits + retries

---

## Website Form Integration

### HTML Form Example
```html
<form action="https://api.sellia.io/api/v1/lead-sources/website/submit-form" method="POST">
  <input name="name" placeholder="Full name" required>
  <input name="email" type="email" placeholder="Email" required>
  <input name="company" placeholder="Company">
  <textarea name="message" placeholder="Message"></textarea>
  <input type="hidden" name="form_source" value="https://example.com/sales">
  <button type="submit">Get Demo</button>
</form>
```

When submitted:
1. Lead created in Leads API
2. Auto-enrolled in configured workflow
3. Email sequence begins immediately

---

## Referral Program

### Referral Link Format
```
https://api.sellia.io/api/v1/lead-sources/referral/submit?
  referrer_name=Jane+Doe
  &referrer_email=jane@example.com
  &referred_name=John+Doe
  &referred_email=john@example.com
  &referred_company=TechCorp
```

Referrals get:
- Higher priority score
- Auto-enrolled in VIP nurture workflow
- Referrer gets tracking/commission capability (v2)

---

## Next Steps (FASE 3+)
- [ ] Real LinkedIn API integration
- [ ] Email enrichment (RocketReach, Hunter)
- [ ] Website form auto-enrollment
- [ ] Referral tracking + commission
- [ ] Lead deduplication
- [ ] SMTP delivery + tracking
- [ ] Lead scoring based on source
- [ ] Source ROI analytics
