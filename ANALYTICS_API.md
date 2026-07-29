# Analytics + Dashboard API - FASE 4

## Overview
Complete business intelligence: funnel, email metrics, lead source ROI, workflow performance, lead health.

**Base URL:** `/api/v1/analytics`

---

## Endpoints

### 1. Sales Funnel
```bash
GET /api/v1/analytics/funnel

Response:
{
  "status": "ok",
  "data": {
    "funnel": {
      "new": 150,
      "contacted": 120,
      "engaged": 45,
      "qualified": 15,
      "won": 3,
      "bounced": 5,
      "unsubscribed": 2,
      "lost": 10
    },
    "total": 350,
    "conversion_rates": {
      "new": 42.86,
      "contacted": 34.29,
      "engaged": 12.86,
      "qualified": 4.29,
      "won": 0.86,
      "bounced": 1.43,
      "unsubscribed": 0.57,
      "lost": 2.86
    },
    "flow": "new → contacted → engaged → qualified → won"
  }
}
```

**Metrics:**
- Total leads per status
- % at each stage
- Conversion rate (stage to next stage)
- Terminal states (won, lost, bounced, unsubscribed)

---

### 2. Email Metrics
```bash
GET /api/v1/analytics/email-metrics

Response:
{
  "status": "ok",
  "data": {
    "total_sent": 1250,
    "delivered": 1100,
    "delivery_rate": 88.0,
    "opened": 450,
    "open_rate": 40.91,
    "clicked": 120,
    "click_rate": 26.67,
    "bounced": 50,
    "bounce_rate": 4.0
  }
}
```

**Metrics:**
- Sent, delivered, bounced counts
- Delivery rate (delivered / sent)
- Open rate (opens / delivered)
- Click rate (clicks / opened)
- Bounce rate (bounces / sent)

---

### 3. Lead Source ROI
```bash
GET /api/v1/analytics/lead-sources

Response:
{
  "status": "ok",
  "data": {
    "by_source": {
      "linkedin": {
        "total_leads": 150,
        "avg_score": 68.5,
        "engaged": 45,
        "engagement_rate": 30.0,
        "qualified": 12,
        "qualification_rate": 8.0,
        "won": 2,
        "conversion_rate": 1.33
      },
      "website": {
        "total_leads": 100,
        "avg_score": 55.2,
        "engaged": 20,
        "engagement_rate": 20.0,
        "qualified": 2,
        "qualification_rate": 2.0,
        "won": 0,
        "conversion_rate": 0.0
      },
      "manual": {
        "total_leads": 100,
        "avg_score": 45.1,
        "engaged": 5,
        "engagement_rate": 5.0,
        "qualified": 1,
        "qualification_rate": 1.0,
        "won": 1,
        "conversion_rate": 1.0
      }
    },
    "total_leads": 350
  }
}
```

**Metrics by Source:**
- Total leads generated
- Average quality (score)
- Engagement rate
- Qualification rate
- Conversion rate (leads → customers)

**ROI Ranking:**
1. LinkedIn (highest conversion, highest engagement)
2. Website (moderate conversion, moderate engagement)
3. Manual (lowest volume, hit-or-miss)

---

### 4. Workflow Performance
```bash
GET /api/v1/analytics/workflow-performance

Response:
{
  "status": "ok",
  "data": {
    "by_workflow": {
      "1": {
        "step_1": {
          "total": 150,
          "sent": 150,
          "open_rate": 35.0,
          "click_rate": 15.0,
          "bounce_rate": 2.0
        },
        "step_2": {
          "total": 150,
          "sent": 135,
          "open_rate": 28.0,
          "click_rate": 10.0,
          "bounce_rate": 1.0
        },
        "step_3": {
          "total": 150,
          "sent": 110,
          "open_rate": 20.0,
          "click_rate": 5.0,
          "bounce_rate": 0.5
        },
        "step_4": {
          "total": 150,
          "sent": 85,
          "open_rate": 15.0,
          "click_rate": 2.0,
          "bounce_rate": 0.2
        }
      }
    }
  }
}
```

**Metrics per Step:**
- Total executions
- Sent/delivered
- Open rate
- Click rate
- Bounce rate

**Performance Trends:**
- Step 1: highest volume, baseline opens (35%)
- Step 2: slight drop-off (28% open rate)
- Step 3: engagement fatigue (20% open rate)
- Step 4: re-engagement email (15% open rate, lowest bounce)

---

### 5. Lead Score Distribution
```bash
GET /api/v1/analytics/lead-score-distribution

Response:
{
  "status": "ok",
  "data": {
    "distribution": {
      "0-20": 95,
      "21-40": 85,
      "41-60": 75,
      "61-80": 65,
      "81-100": 30
    },
    "total_leads": 350,
    "avg_score": 42.1,
    "max_score": 95,
    "min_score": 0
  }
}
```

**Insights:**
- 30 high-quality leads (81-100 score)
- 65 good leads (61-80 score)
- 255 lower-quality leads (0-60 score)
- Opportunity: focus efforts on top 30 (high ROI)

---

### 6. Time Series (Daily Metrics)
```bash
GET /api/v1/analytics/time-series?days=30

Response:
{
  "status": "ok",
  "data": {
    "leads_by_day": {
      "2026-07-01": 5,
      "2026-07-02": 3,
      "2026-07-03": 8,
      ...
      "2026-07-29": 12
    },
    "emails_by_day": {
      "2026-07-01": 150,
      "2026-07-02": 145,
      ...
      "2026-07-29": 320
    },
    "period_days": 30
  }
}
```

**Use Cases:**
- Campaign performance tracking
- Weekly trends (Mon-Fri vs weekends)
- Email volume over time
- Lead generation velocity

---

### 7. Lead Health Segmentation
```bash
GET /api/v1/analytics/lead-health

Response:
{
  "status": "ok",
  "data": {
    "hot": {
      "count": 12,
      "leads": [
        { "id": 42, "name": "John Doe", "company": "Acme", "score": 85, "days_since_contact": 1 },
        { "id": 43, "name": "Jane Smith", "company": "TechCorp", "score": 78, "days_since_contact": 2 },
        ...
      ]
    },
    "warm": {
      "count": 35,
      "leads": [
        { "id": 44, "name": "Bob Wilson", "company": "StartupX", "score": 65, "days_since_contact": 4 },
        ...
      ]
    },
    "cold": {
      "count": 250,
      "leads": [...]
    },
    "dead": {
      "count": 53,
      "leads": [
        { "id": 100, "name": "Old Lead", "email": "old@example.com", "company": "Defunct", "status": "bounced" },
        ...
      ]
    },
    "total": 350
  }
}
```

**Segmentation:**
- **Hot (12):** score ≥ 70, contacted < 3 days ago → call/meeting NOW
- **Warm (35):** score 40-69, contacted < 7 days ago → nurture sequence
- **Cold (250):** score < 40 OR contacted > 7 days ago → re-engagement
- **Dead (53):** bounced/unsubscribed/lost → cleanup/removal

**Action Items:**
1. Focus sales team on Hot leads
2. Continue nurture for Warm leads
3. Trigger no-engagement emails for Cold leads
4. Remove Dead leads from active campaigns

---

### 8. Complete Dashboard Summary
```bash
GET /api/v1/analytics/summary

Response:
{
  "status": "ok",
  "data": {
    "funnel": { ... },
    "email_metrics": { ... },
    "lead_sources": { ... },
    "workflow_performance": { ... },
    "lead_health": { ... },
    "timestamp": "2026-07-29T16:30:00"
  }
}
```

**One-Stop View:**
- All key metrics in single request
- Dashboard refresh frequency: 5 minutes
- Use for executive reporting

---

## Dashboard Mockup

```
┌─────────────────────────────────────────────────────────┐
│ SellIA Dashboard                              Last 30 days
├─────────────────────────────────────────────────────────┤

┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ Leads       │  │ Emails      │  │ Conversion  │
│ 350 total   │  │ 1,250 sent  │  │ 0.86%       │
│ ↑ 12 today  │  │ 88% deliv.  │  │ (11 deals)  │
└─────────────┘  └─────────────┘  └─────────────┘

┌──────────────────────────────────────────────────────┐
│ Sales Funnel                                         │
│ ████████████████ 150 new                             │
│ ████████████     120 contacted (80%)                 │
│ ██████           45 engaged (37%)                    │
│ ██               15 qualified (33%)                  │
│ █                3 won (20%)                         │
└──────────────────────────────────────────────────────┘

┌──────────────────┐  ┌──────────────────┐
│ Email Metrics    │  │ Lead Quality     │
│                  │  │                  │
│ Delivery: 88%    │  │ Hot:   12 ★★★★★ │
│ Open:     40.9%  │  │ Warm:  35 ★★★★  │
│ Click:    26.7%  │  │ Cold:  250 ★★    │
│ Bounce:   4.0%   │  │ Dead:  53 ★      │
└──────────────────┘  └──────────────────┘

┌──────────────────────────────────────────────────────┐
│ Best Source: LinkedIn                               │
│ ✓ 150 leads | 30% engagement | 1.33% conversion   │
└──────────────────────────────────────────────────────┘
```

---

## KPIs Summary

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Lead Generation | 50/week | 42/week | ⚠️ -16% |
| Email Delivery | 90% | 88% | ✓ Good |
| Open Rate | 35% | 40.9% | ✓ Excellent |
| Click Rate | 20% | 26.7% | ✓ Excellent |
| Conversion Rate | 2% | 0.86% | ⚠️ Below target |
| Lead Quality Avg | 50+ | 42.1 | ⚠️ Below target |
| Sales Cycle | 21 days | 28 days | ⚠️ Slowing |

---

## Next Steps (FASE 4.2+)

- [ ] Cohort analysis (by acquisition month)
- [ ] LTV + CAC calculations
- [ ] Pipeline forecast
- [ ] A/B testing framework
- [ ] Email template rankings
- [ ] Lead scoring model validation
- [ ] Predictive churn model
- [ ] Real-time dashboard (WebSocket)

