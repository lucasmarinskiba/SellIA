# SellIA Lead Management API

## Overview
Lead database + automatic scoring system integrado en SellIA Sellbot.

**Base URL:** `/api/v1/leads`

## Features

### 1. Lead Database
- Store leads con todos datos: email, phone, company, budget, timeline, etc.
- Status tracking: new → contacted → qualified → negotiating → closed/lost
- Metadata: source (linkedin, website, cold-email, referral), pain points, notes

### 2. Automatic Scoring (0-100)
Factors:
- **Completeness (10%)**: Qué datos están completos (email, phone, company, job_title, industry, budget)
- **Engagement (30%)**: Si fue contactado, referral, website lead
- **Fit Score (60%)**: Ideal Customer Profile match
  - Budget fit (SaaS deals >$5k son mejor)
  - Timeline fit (immediate > 3-6 months)
  - Industry fit (SaaS/Tech preferred)
  - Company size fit (SMB/Mid-market preferred)

**Score Breakdown Example:**
```json
{
  "score": 78.5,
  "breakdown": {
    "completeness": 0.9,
    "engagement": 0.8,
    "fit": 0.75
  },
  "reasons": [
    "✅ Datos completos",
    "✅ Buen fit con perfil ideal",
    "💰 Budget: $50,000",
    "⚡ Timeline inmediato"
  ]
}
```

---

## Endpoints

### 1. Create Lead
```
POST /api/v1/leads
Content-Type: application/json

{
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+1-234-567-8900",
  "company": "Acme Corp",
  "industry": "SaaS",
  "job_title": "CTO",
  "pain_points": "Manual sales process, low conversion",
  "budget": 50000,
  "timeline": "immediate",
  "source": "linkedin",
  "notes": "Warm intro from Sarah"
}

Response:
{
  "id": 1,
  "name": "John Doe",
  "email": "john@example.com",
  "score": 78.5,
  "status": "new",
  "created_at": "2026-07-29T17:30:00",
  "updated_at": "2026-07-29T17:30:00",
  "last_contacted": null,
  ...
}
```

### 2. List Leads
```
GET /api/v1/leads?skip=0&limit=50&min_score=60&status=contacted

Response:
[
  { id: 1, name: "John Doe", email: "...", score: 78.5, status: "contacted", ... },
  { id: 2, name: "Jane Smith", email: "...", score: 72.0, status: "new", ... },
  ...
]

Query Params:
- skip: Pagination offset (default 0)
- limit: Max results (default 50)
- min_score: Filter by minimum score (default 0)
- status: Filter by status (new|contacted|qualified|negotiating|closed|lost)
```

### 3. Get Lead Details
```
GET /api/v1/leads/{lead_id}

Response:
{
  "id": 1,
  "name": "John Doe",
  "email": "john@example.com",
  "score": 78.5,
  "status": "contacted",
  ...
}
```

### 4. Update Lead
```
PUT /api/v1/leads/{lead_id}
Content-Type: application/json

{
  "status": "qualified",
  "budget": 75000,
  "notes": "Added more context from discovery call"
}

Response:
{
  "id": 1,
  "score": 82.0,  # Score actualizado automáticamente
  "status": "qualified",
  ...
}
```

### 5. Mark as Contacted
```
POST /api/v1/leads/{lead_id}/contact

Response:
{
  "id": 1,
  "status": "contacted",
  "last_contacted": "2026-07-29T17:35:00",
  "score": 85.0,  # Score sube por engagement
  ...
}
```

### 6. Rescore Lead
```
POST /api/v1/leads/{lead_id}/score

Response:
{
  "lead_id": 1,
  "score": 78.5,
  "score_breakdown": {
    "completeness": 0.9,
    "engagement": 0.8,
    "fit": 0.75
  },
  "reasons": ["✅ Datos completos", "💰 Budget: $50,000", ...],
  "scored_at": "2026-07-29T17:36:00"
}
```

### 7. Get Stats
```
GET /api/v1/leads/stats/summary

Response:
{
  "total": 145,
  "by_status": {
    "new": 45,
    "contacted": 32,
    "qualified": 28,
    "negotiating": 15,
    "closed": 22,
    "lost": 3
  },
  "avg_score": 72.3,
  "high_quality": 68  # Score >= 70
}
```

---

## Integration with SellIA Workflows

### Cold Email Integration
```python
# 1. Create lead
POST /api/v1/leads
{ name: "John", email: "john@example.com", ... }

# 2. Generate cold email sequence
POST /api/v1/sequences/cold-email
{ lead: {...}, offer: "SellIA Platform" }

# 3. Track engagement
POST /api/v1/leads/{lead_id}/contact
# Score sube automáticamente
```

### WhatsApp Integration
```python
# 1. Crear lead desde WhatsApp conversation
POST /api/v1/leads
{ phone: "+1-xxx-xxx-xxxx", source: "whatsapp", ... }

# 2. Send WhatsApp via SellIA
POST /api/v1/webhooks/whatsapp
# IA responde, engagement sube

# 3. Track progression
PUT /api/v1/leads/{lead_id}
{ status: "qualified", notes: "..." }
```

---

## Scoring Rules Detail

### Completeness Score (10% of total)
```
Fields: email, phone, company, job_title, industry, budget
Scoring: (filled_fields / 6) * 100
Example: 4/6 fields = 67% completeness
```

### Engagement Score (30% of total)
```
- Contacted: +50 points
- Has last_contacted: +25 points
- Source is website/referral: +25 points
Max: 100 points
Example: Contacted via referral = 75 engagement score
```

### Fit Score (60% of total)
```
Budget:
  - >= $5k: 30 points
  - >= $1k: 20 points
  - < $1k: 10 points

Timeline:
  - immediate: 25 points
  - 3-6 months: 15 points

Industry (SaaS/Tech/Startup preferred):
  - Yes: 20 points
  - No: 5 points

Company size:
  - SMB/Mid-market: 5 points

Max: 100 points
```

### Final Score Formula
```
SCORE = (Completeness * 0.10) + (Engagement * 0.30) + (Fit * 0.60)
Range: 0-100
Interpretation:
  - 80+: Hot lead, close now
  - 60-79: Warm lead, nurture
  - 40-59: Cool lead, follow up later
  - <40: Not qualified yet
```

---

## Storage
Currently: In-memory dict (resets on server restart)
Next Phase: PostgreSQL + persistent storage

---

## Examples

### Example 1: Quick Lead Creation
```bash
curl -X POST http://localhost:8000/api/v1/leads \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sarah Johnson",
    "email": "sarah@techstartup.io",
    "company": "TechStartup Inc",
    "industry": "SaaS",
    "job_title": "VP Sales",
    "budget": 50000,
    "timeline": "immediate",
    "source": "linkedin"
  }'
```

### Example 2: Filter High-Quality Leads
```bash
curl http://localhost:8000/api/v1/leads?min_score=70&status=new
```

### Example 3: Update Lead Status After Conversation
```bash
curl -X PUT http://localhost:8000/api/v1/leads/1 \
  -H "Content-Type: application/json" \
  -d '{
    "status": "qualified",
    "notes": "Discussed 3-month pilot program"
  }'
```

---

## Next Steps (FASE 3+)
- [ ] PostgreSQL persistence
- [ ] Lead enrichment (company data, technographics)
- [ ] Email + SMS workflow automation
- [ ] LinkedIn scraper for lead generation
- [ ] Lead distribution rules (round-robin, auto-assignment)
- [ ] Activity timeline (calls, emails, meetings)
- [ ] Custom scoring models per industry
