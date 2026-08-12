# Phase 27 Deployment Execution Guide

**Status**: Ready for production deployment  
**Target Date**: Sep 26, 2026  
**Duration**: 2 weeks (Sep 12-25 prep, Sep 26 deployment)

---

## 1️⃣ DATABASE MIGRATION

### Prerequisites
- PostgreSQL 13+ running
- Alembic installed (`pip install alembic sqlalchemy`)
- Database credentials configured in `.env`

### Execution

```bash
# 1. Backup current database
pg_dump $DATABASE_URL > backup_$(date +%s).sql

# 2. Run migrations
cd backend
alembic upgrade head

# 3. Verify tables created
psql $DATABASE_URL -c "\dt" | grep -E "deal_stakeholders|deal_probability|deal_health|stakeholder_engagement|model_predictions_cache|email_verification|account_approval|email_templates"

# Expected output: 10 tables, 30+ indexes
```

### Rollback (if needed)
```bash
# Go back 1 revision
alembic downgrade -1

# Go back 2 revisions
alembic downgrade -2
```

---

## 2️⃣ ML MODEL TRAINING

### Generate Training Data

```python
# backend/scripts/train_model.py
import pickle
from pathlib import Path
from backend.app.domains.ml.deal_probability_model import DealProbabilityModel

# Load 500+ historical deals from database
db = SessionLocal()
deals = db.query(Deal).filter(Deal.closed_at != None).limit(500).all()

# Extract training labels (0=lost, 1=won)
training_labels = [1 if deal.status == "won" else 0 for deal in deals]

# Prepare deal data dicts
training_data = [
    {
        "created_at": deal.created_at,
        "stage_entered_at": deal.stage_entered_at,
        "value": deal.amount,
        "stakeholders": [...],  # From deal_stakeholders table
        "engagement_events": [...],  # From stakeholder_engagement_events
        "proposal_sent_at": deal.proposal_sent_at,
        "budget_confirmed": deal.budget_confirmed,
        "timeline_confirmed": deal.timeline_confirmed,
        "competitor_mentions": [],
        "avg_buyer_response_time_hours": 48,
    }
    for deal in deals
]

# Train model
model = DealProbabilityModel()
metrics = model.train(
    training_data=training_data,
    training_labels=training_labels,
    validation_data=training_data[400:],  # Last 100 for validation
    validation_labels=training_labels[400:],
)

print(f"Training complete. AUC: {metrics['auc_score']}")

# Save model
model.save_model("backend/app/domains/ml/models/deal_probability_model.pkl")
```

### Run Training
```bash
cd backend
python scripts/train_model.py

# Output:
# Training model on 400 deals...
# [0]     validation-logloss: 0.52340  logloss: 0.53210
# [100]   validation-logloss: 0.38910  logloss: 0.39840
# ...
# Training complete. AUC: 0.8624
# Saved model to backend/app/domains/ml/models/deal_probability_model.pkl
```

**Success Criteria**: AUC ≥ 0.85 on validation set

---

## 3️⃣ INTEGRATION TESTING

### Unit Tests

```bash
cd backend
pytest tests/test_deal_intelligence.py -v

# Expected: 50+ tests passing
# Coverage: >80% on deal_intelligence.py, email_auth.py
```

### Integration Tests

```bash
cd backend

# Test 1: Email verification flow
pytest tests/integration/test_email_verification.py -v

# Test 2: Account approval workflow
pytest tests/integration/test_account_approval.py -v

# Test 3: Deal intelligence pipeline
pytest tests/integration/test_deal_intelligence_e2e.py -v

# Test 4: ML model inference
pytest tests/integration/test_probability_model.py -v

# Test 5: API endpoints
pytest tests/integration/test_deal_intelligence_api.py -v
```

### Load Testing

```bash
# Simulate 100 concurrent dashboard users
locust -f tests/load/locustfile.py --host=http://localhost:8000 -u 100 -r 10 --run-time 5m

# Success criteria:
# - 95th percentile response: <500ms
# - Error rate: <1%
# - Throughput: >200 req/s
```

---

## 4️⃣ UAT WITH POWER USERS

### Setup (Sep 12-13)

1. **Environment**:
   - Staging database with 1000+ test deals
   - Fresh user accounts for 5 power users
   - Phase 27 dashboard deployed to staging

2. **Test Data**:
   - 20 deals in "opportunity" stage
   - 200+ stakeholders across deals
   - 500+ engagement events

3. **Training** (1 day):
   - Show power users 30-min walkthrough
   - Provide user guide (PDF)
   - Demo recommended workflow

### Execution (Sep 14-24, 2 weeks)

**Week 1: Functionality Testing**
- [ ] Day 1-2: Dashboard loads, data displays correctly
- [ ] Day 3-4: Stakeholder mapping accurate (identify economic buyers)
- [ ] Day 5: Probability predictions make sense (compare to rep forecasts)
- [ ] Week 1 end: Health scoring reflects deal reality

**Week 2: Workflow Testing**
- [ ] Day 1-2: Engagement tracking works (rep actions → engagement updates)
- [ ] Day 3-4: Recommendations are actionable (reps take actions)
- [ ] Day 5: Email alerts working (reps get notified)
- [ ] Week 2 end: 5+ reps using daily

### Success Criteria
- ✅ 95%+ uptime (no crashes)
- ✅ <2s dashboard load (all 4 components)
- ✅ 5+ reps using daily
- ✅ Zero P0 bugs (critical)
- ✅ <5 P1 bugs (major, non-blocking)
- ✅ Forecast accuracy +10% (vs current)

### Feedback Loop
- Daily standup (15 min)
- Bugs logged in Linear
- Feature requests documented
- Weekly review call

---

## 5️⃣ PRODUCTION DEPLOYMENT (Sep 26)

### Pre-Deployment Checklist

**Code**:
- [ ] All tests passing (unit + integration + load)
- [ ] Code reviewed (2+ approvals)
- [ ] No critical security issues (SAST scan)
- [ ] Staging environment fully tested

**Infrastructure**:
- [ ] PostgreSQL 13+ ready
- [ ] Redis running (cache)
- [ ] Celery workers scaled (3+ workers)
- [ ] Monitoring/alerting configured

**Rollback Plan**:
- [ ] Backup of production DB taken
- [ ] Previous schema version saved
- [ ] Rollback script tested: `alembic downgrade -2`
- [ ] Communication plan: Slack channel + status page

**Documentation**:
- [ ] User guide published
- [ ] Admin guide (email templates, approvals)
- [ ] API docs (Swagger/OpenAPI)
- [ ] Troubleshooting guide

### Deployment Steps

**Morning (6 AM-8 AM, before market open)**:

```bash
# 1. Maintenance window notification
# Slack: "Phase 27 deployment starting. ETA 2 hours. Feature available 8 AM."

# 2. Stop user traffic
# Mark feature flag as "maintenance"

# 3. Backup database
pg_dump $PROD_DB_URL > /backups/prod_before_phase27_$(date +%s).sql

# 4. Run migrations
cd backend
alembic upgrade head

# 5. Verify schema
psql $PROD_DB_URL -c "\d deal_stakeholders" | head -20

# 6. Load pre-trained ML model
# Copy model from staging to production
cp staging_models/deal_probability_model.pkl /prod/models/

# 7. Verify model inference
# Test with 5 sample deals

# 8. Deploy backend
docker pull sellia/backend:phase27-prod
docker service update --image sellia/backend:phase27-prod sellia-backend

# 9. Deploy frontend
npm run build && npm run export
aws s3 sync out/ s3://sellia-frontend-prod/

# 10. Smoke tests
# 5 manual tests on production
# - Create stakeholder
# - Record engagement
# - Check probability prediction
# - View health score
# - Admin approves account

# 11. Feature flag: enable
# Mark feature as "live"

# 12. Monitor
# Dashboard, logs, error rate for 1 hour
```

### Monitoring (Hour 1-2)

```bash
# Watch error rate
curl http://prod-api/health
curl http://prod-api/metrics

# Check logs
docker logs sellia-backend | grep -i error

# Monitor Celery tasks
celery -A backend.celery_app inspect active

# Check database performance
psql $PROD_DB_URL -c "SELECT * FROM pg_stat_statements LIMIT 20;"

# CPU/Memory/Network
docker stats

# Success criteria:
# - Error rate: <0.1%
# - API p95: <500ms
# - Celery queue: <10s backlog
# - Zero critical alerts
```

### Rollback (if issues detected)

```bash
# 1. Disable feature
# Set feature flag to "maintenance"

# 2. Stop backend service
docker service scale sellia-backend=0

# 3. Rollback schema
alembic downgrade -2

# 4. Restore frontend
aws s3 sync s3://sellia-frontend-backups/pre-phase27/ s3://sellia-frontend-prod/

# 5. Start backend with previous image
docker pull sellia/backend:latest
docker service scale sellia-backend=3

# 6. Verify
curl http://prod-api/health

# 7. Communicate
# Slack: "Phase 27 deployment rolled back. Investigating issue. ETA 1 hour for second attempt."
```

---

## 📊 Success Metrics (Post-Deployment)

**Week 1**:
- ✅ 50+ reps using dashboard
- ✅ 500+ deals with intelligence data
- ✅ 10,000+ engagement events recorded
- ✅ <2s dashboard load time
- ✅ 95%+ uptime

**Week 2-4**:
- ✅ Forecast accuracy +15% (vs pre-Phase 27)
- ✅ Deal health insights used in 80%+ of deals
- ✅ Stalled deals identified 7-10 days earlier
- ✅ $500k+ pipeline retained (better forecasting)

---

## 🆘 Support & Escalation

**During Deployment (Sep 26 7 AM - 12 PM)**:
- On-call engineer: [name]
- Slack channel: #phase27-deployment
- War room: [video link]

**Post-Deployment**:
- Product team: Monitors adoption
- Support team: Handles user questions
- Engineering: On standby for bugs

**Issue Escalation**:
1. P0 (production down): Immediate rollback
2. P1 (feature broken): Hotfix or rollback within 1 hour
3. P2 (degraded): Fix within business hours
4. P3 (minor): Fix in next sprint

---

## 📝 Sign-Off Checklist

**Before Deployment**:
- [ ] CTO approves architecture
- [ ] Product approves feature set
- [ ] QA approves test results
- [ ] Security approves scan results
- [ ] Operations approves infrastructure

**After Deployment**:
- [ ] VP Sales confirms team can use
- [ ] Finance confirms no budget overruns
- [ ] CEO confirms launch timing

---

**Target Deployment**: Sep 26, 2026 6 AM  
**Estimated Duration**: 2 hours  
**Rollback Available**: Yes (within 5 minutes)
