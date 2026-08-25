# Real Data Wiring for SellIA Dashboard

Every user now sees 100% real data, interactions, numbers, and metrics tailored to their business.

## Dashboard Data Sources (Per User)

Each user's dashboard pulls real data from these endpoints:

### 1. **KPIs (Top Section)**
```
GET /api/v1/brain/kpis
```
- **Leads Activos**: Count of active leads in user's pipeline
- **Pipeline Activo**: Sum of deal values in sales stages
- **Tasa Conversión**: % of leads → customers (calculated from conversions table)
- **Revenue (24h/7d)**: Sum of recent orders, real transactions

**Source**: `leads` + `conversions` tables, aggregated by business_id

---

### 2. **Escuadrones (AI Teams Executing)**
```
GET /api/v1/brain/squads
```
- Shows AI agents actively working on user's leads
- Real-time execution status per lead
- Minutes spent, conversations count, next action

**Source**: `agent_executions` + `leads` join

---

### 3. **Pipeline de Ventas (Sales Pipeline)**
```
GET /api/v1/brain/pipeline-summary
```
- Real pipeline stages: Discovery → Proposal → Negotiation → Won
- Count + value per stage
- Forecast based on historical close rates

**Source**: `leads` grouped by stage + `conversions` for historical data

---

### 4. **Agent Audit Log (Real-Time Actions)**
```
GET /api/v1/brain/audit-log
```
- Live feed of AI agent actions: emails sent, messages, decisions
- Sortable by timestamp, agent, lead
- Shows actual system behavior in real-time

**Source**: `computer_use_audit_logs` table, filtered to user's business leads

---

### 5. **Notificaciones (Real Alerts)**
```
GET /api/v1/brain/notifications
```
- Real alerts: high-value lead detected, response needed, deal at risk
- Timestamp, severity, action link
- Cleared when user acts

**Source**: `notifications` + `alert_rules` tables

---

## How to Enable Real Data

### For Your Own User (Dev)

1. **Create a business**:
```bash
POST /api/v1/businesses
{
  "name": "My Test Business",
  "description": "E-commerce + retail",
  "website": "mysite.com"
}
```

2. **Add locations (Phase 5A)**:
```bash
POST /api/v1/businesses/{business_id}/locations
{
  "name": "Showroom Centro",
  "type": "showroom",
  "address": "Av. Corrientes 1234",
  "city": "Buenos Aires",
  "latitude": -34.6037,
  "longitude": -58.3816,
  "hours_json": {
    "monday": {"open": "09:00", "close": "18:00"},
    ...
  }
}
```

3. **Add test leads**:
```bash
POST /api/v1/leads
{
  "email": "prospect@company.com",
  "first_name": "Juan",
  "company": "TechCorp",
  "score": 85,
  "stage": "proposal"
}
```

4. **Log offline conversions (Phase 5B)**:
```bash
POST /api/v1/proximity/log-visit
{
  "location_id": "uuid...",
  "latitude": -34.6037,
  "longitude": -58.3816,
  "visit_type": "demo"
}
```

5. **Refresh dashboard** at https://sellia-brain.vercel.app/sellia-brain
   - All KPIs now show real numbers
   - Pipeline shows real stages
   - Audit log shows real agent actions

---

## Production Data Flow

### For Production (Railway Backend)

SellIA reads real data from PostgreSQL:

1. **User signs up** → new row in `users` table
2. **User adds business** → `businesses` row linked to user_id
3. **User creates leads** → `leads` rows with business_id
4. **AI agents work** → `agent_executions` logged + `computer_use_audit_logs`
5. **Dashboard queries** → filters by current_user.id → business_id → real data

**Each user only sees their own data** (user_id filter in auth middleware).

---

## Real Data Guarantees

✅ **No mocking**: All dashboard numbers come from actual database rows
✅ **Per-user isolation**: User A never sees User B's leads/metrics
✅ **Real-time updates**: Dashboard polls fresh data every 20s
✅ **Honest zeroes**: If no leads → shows 0, not "--" or fake numbers
✅ **100% coverage**: All 7 dashboard sections source real data

---

## API Endpoints Summary

| Section | Endpoint | Returns |
|---------|----------|---------|
| KPIs | `GET /api/v1/brain/kpis` | leads, revenue, conversion rate |
| Squads | `GET /api/v1/brain/squads` | active agents + execution status |
| Pipeline | `GET /api/v1/brain/pipeline-summary` | stage breakdown + forecast |
| Audit Log | `GET /api/v1/brain/audit-log` | real agent actions (live) |
| Notifications | `GET /api/v1/brain/notifications` | active alerts |
| Locations | `GET /api/v1/businesses/{id}/locations` | Phase 5A |
| Proximity | `GET /api/v1/proximity/check-nearby` | Phase 5B |

---

## Testing the Real-Data System

### Local Development
1. Start backend: `python -m uvicorn app.main:app --reload`
2. Start frontend: `npm run dev`
3. Create test lead: `curl -X POST http://localhost:8000/api/v1/leads ...`
4. Check dashboard: http://localhost:3000/sellia-brain
5. All sections show live data instantly

### Production (Vercel)
1. Sign in at https://sellia-brain.vercel.app/
2. Add business → real data populated
3. Dashboard auto-refreshes every 20s
4. All metrics are real, per-user

---

## Next Steps

- [ ] Wire up offline conversion analytics (Phase 5C)
- [ ] Google Business Profile sync (Phase 5C)
- [ ] Proximity-based automation triggers (Phase 5D)
- [ ] Real-time foot traffic dashboard (Phase 5D)
