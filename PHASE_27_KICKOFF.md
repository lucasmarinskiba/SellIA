# Phase 27 - Sprint Kickoff & Execution Guide

**Start Date**: Monday, August 12, 2026  
**Duration**: 8 weeks (40 working days)  
**Team**: 3 engineers (1 backend, 1 ML, 1 frontend)  
**Goal**: Deal Intelligence Foundation Live

---

## PRE-SPRINT SETUP (Friday Before)

### 1. Environment Setup
```bash
# Backend
cd backend/
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install pytest pytest-cov sqlalchemy joblib xgboost pandas numpy

# Frontend
cd frontend/
npm install

# ML
pip install scikit-learn matplotlib seaborn

# Verify versions
python --version  # 3.11+
npm --version    # 18+
pytest --version # 8+
```

### 2. Database Preparation
```bash
# Test migrations locally
cd backend/
alembic upgrade head

# Verify schema created
psql -U sellia_user -d sellia -c "\dt intelligence.*"
```

### 3. Git Setup
```bash
# Create feature branch
git checkout -b feature/phase-27-deal-intelligence

# Create tracking branch
git branch phase-27-staging origin/main
```

### 4. Tooling
```bash
# Install monitoring
pip install black flake8 pylint

# Pre-commit hooks
pip install pre-commit
pre-commit install

# VS Code extensions
# - Python
# - Pylance
# - SQLTools
# - Thunder Client (API testing)
```

---

## SPRINT 1: DATABASE + SCHEMA (Week 1-2)

### Sprint Goal
Schema + migrations deployed, ORM models complete, base infrastructure ready.

### Day 1-5: Schema Design

**Day 1: Schema Review**
- [ ] Team reviews `PHASE_27_ARCHITECTURE.md` database section (30 min)
- [ ] Review 6 tables, 11 indexes, relationships
- [ ] Identify potential N+1 queries
- [ ] Create PR: `schema-design-review`

**Day 2: Alembic Migration**
```bash
# Create migration file
alembic revision --autogenerate -m "Create intelligence schema"

# Edit migration to add custom SQL (indexes, grants)
vim alembic/versions/0031_intelligence_schema.py

# Test upgrade
alembic upgrade head
alembic downgrade -1
alembic upgrade head
```
- [ ] Migration created + tested
- [ ] Verify upgrade/downgrade idempotent

**Day 3: ORM Models**
```bash
# Create models file
touch backend/app/models/intelligence.py

# Add 6 models (copy from PHASE_27_CODE_EXAMPLES.md)
# - DealStakeholder
# - DealProbabilityScore
# - DealHealthSnapshot
# - DealHealthAlert
# - StakeholderEngagementEvent
# - ModelPredictionsCache

# Verify syntax
python -m py_compile backend/app/models/intelligence.py
```
- [ ] Models created + type hints
- [ ] Relationships defined
- [ ] Docstrings added

**Day 4: Test Fixtures**
```bash
# Create fixture file
touch tests/fixtures/intelligence_fixtures.py

# Add 5 fixtures
# - sample_deal
# - sample_stakeholders
# - sample_engagement_events
# - sample_health_snapshot
# - sample_alerts

# Run fixture tests
pytest tests/fixtures/intelligence_fixtures.py -v
```
- [ ] Fixtures working
- [ ] Parametrized tests created

**Day 5: Sprint 1 Review**
- [ ] All schema + migration tests passing (pytest -v)
- [ ] Code review: team approval
- [ ] Merge to `phase-27-staging` branch
- [ ] Demo to product: show database structure

### Deliverables (Day 5 EOD)
```
✅ Alembic migration (0031_intelligence_schema.py)
✅ 6 ORM models (backend/app/models/intelligence.py)
✅ 5 test fixtures (tests/fixtures/intelligence_fixtures.py)
✅ All tests passing (pytest tests/fixtures/ -v)
```

### Day 6-10: Integration + Validation

**Day 6: Webhook Receivers**
- [ ] Email tracking webhook receiver (POST /webhooks/email-tracking)
- [ ] Salesforce webhook receiver (POST /webhooks/salesforce/deal-update)
- [ ] Signature validation (HMAC-SHA256)
- [ ] Test with mock payloads

**Day 7: Stakeholder Enrichment**
- [ ] Service to hydrate stakeholders from CRM
- [ ] Fetch title, email, company from Salesforce
- [ ] Cache enrichment (avoid duplicate API calls)
- [ ] Test: 10 stakeholders enriched

**Day 8: Engagement Event Ingestion**
- [ ] Parse email_open, email_click, call, meeting events
- [ ] Map event_type → engagement_value points
- [ ] Batch insert for performance
- [ ] Test: 100 events ingested in < 1s

**Day 9: Health Snapshot Baseline**
- [ ] Script to calculate baseline health for all deals
- [ ] Insert first snapshot per deal
- [ ] Verify distribution (should have wide range: 10-95)
- [ ] Run: `python scripts/calculate_baseline_health.py`

**Day 10: Documentation + Sprint Review**
- [ ] Schema wiki page (relationships + purposes)
- [ ] API spec (preliminary, 5 endpoints)
- [ ] Integration guide (webhooks, format)
- [ ] Demo to team: "Database foundation complete"

### Deliverables (Day 10 EOD)
```
✅ Webhook receivers (email, Salesforce)
✅ Stakeholder enrichment service
✅ Engagement event ingestion pipeline
✅ Baseline health for all deals
✅ Schema documentation
```

---

## SPRINT 2: BACKEND CORE LOGIC (Week 3-4)

### Sprint Goal
DealIntelligenceManager fully implemented + tested (80%+ coverage).

### Daily Breakdown

**Day 11: Stakeholder Intelligence**
```python
# Implement in backend/app/domains/enterprise/deal_intelligence.py
# Methods:
# - get_buying_committee(deal_id) → List[StakeholderProfile]
# - identify_economic_buyer(deal_id) → Optional[StakeholderProfile]
# - _calculate_engagement_score(deal_id, person_id) → float
# - update_stakeholder_engagement() → None

# Test with 5 deals (various committee sizes)
pytest tests/test_deal_intelligence_manager.py::test_get_buying_committee -v
pytest tests/test_deal_intelligence_manager.py::test_identify_economic_buyer_* -v
```
- [ ] 3 methods implemented + tested
- [ ] Handles empty committees gracefully
- [ ] Economic buyer ranking works (C-level > influence > engagement)

**Day 12: Engagement Tracking**
```python
# Implement:
# - update_stakeholder_engagement() - records event + updates score
# - _get_engagement_points(event_type) → int
# - event processor (batch inserts)

# Test event types: email_open (1pt), call (8pt), meeting (10pt)
pytest tests/test_deal_intelligence_manager.py::test_update_*engagement* -v
```
- [ ] All event types mapping correct points
- [ ] Engagement score recalculated on new event
- [ ] 1000 events processed in < 5s

**Day 13: Health Scoring - Part 1**
```python
# Implement component scores:
# - _score_engagement() → 0-100
# - _score_momentum() → 0-100
# - _score_buyer_completeness() → 0-100

# Test various deal states
pytest tests/test_deal_intelligence_manager.py::test_score_* -v
```
- [ ] Each component score 0-100
- [ ] Engagement = avg stakeholder engagement
- [ ] Momentum = days since last activity
- [ ] Buyer = economic buyer + committee size

**Day 14: Health Scoring - Part 2**
```python
# Implement:
# - _score_competition() → 0-100
# - calculate_deal_health() → DealHealth (orchestrator)
# - _generate_recommendations() → List[Dict]

# Test 10 deals (various stages)
pytest tests/test_deal_intelligence_manager.py::test_calculate_deal_health* -v
```
- [ ] Competition scoring (inverse: no competitor = 100)
- [ ] Overall health = weighted avg (E:25%, Mom:25%, Buyer:30%, Comp:20%)
- [ ] Status mapping: 80+ = healthy, 50-80 = at_risk, <50 = critical
- [ ] Recommendations generated (missing buyer, low engagement, etc)

**Day 15: Error Handling + Validation**
```python
# Add error handling:
# - Missing deal → HTTPException 404
# - Invalid event_type → log warning, skip
# - Empty committees → engagement_score = 0
# - N+1 query prevention → use eager loading

pytest tests/test_deal_intelligence_manager.py -v
```
- [ ] All edge cases handled
- [ ] Graceful degradation (no crashes)
- [ ] No N+1 queries (profile with django-silk or SQLAlchemy echo)

**Day 16-20: Unit + Integration Testing**

**Day 16: Unit Tests**
```bash
# Write 30+ unit tests
# coverage: 80%+ target

pytest tests/test_deal_intelligence_manager.py \
  -v --cov=backend/app/domains/enterprise/deal_intelligence \
  --cov-report=html

# Expected: 30+ tests passing, 80%+ coverage
```

**Day 17: Integration Tests**
```bash
# Test end-to-end flows
# - engagement_event → health_recalc
# - stakeholder_add → economic_buyer_identification
# - health_drop → alert_creation

pytest tests/test_deal_intelligence_integration.py -v
```

**Day 18: Performance Testing**
```bash
# Profile slow queries
python -m cProfile -s cumtime backend/test_performance.py

# Target: health_calc < 500ms per deal
# Optimize queries, add indexes if needed
```

**Day 19: Caching Layer**
```python
# Implement Redis caching:
# - health_score cache (1 hour)
# - engagement_score cache (30 min)
# - prediction cache (6 hours)

# Verify cache hits > 80%
pytest tests/test_caching.py -v
```

**Day 20: Sprint 2 Review**
```bash
# Final verification
pytest tests/test_deal_intelligence_manager.py -v \
  --cov=backend/app/domains/enterprise/deal_intelligence \
  --cov-report=term-missing

# Expected: All tests passing, 80%+ coverage
# Code review: team approval
# Merge to main
```

### Deliverables (Day 20 EOD)
```
✅ DealIntelligenceManager (400 lines)
✅ 30+ unit tests (80%+ coverage)
✅ 5+ integration tests
✅ Performance verified (< 500ms per deal)
✅ Caching layer (Redis)
✅ Code reviewed + merged
```

---

## SPRINT 3: ML MODEL TRAINING (Week 5-6)

### Daily Breakdown

**Day 21: Data Preparation**
```python
# Query 2-year deal history
# SELECT * FROM deals WHERE closed_date IS NOT NULL OR lost_date IS NOT NULL

# Create training set (500-1000 deals)
# Label: closed within 90 days = 1, else = 0

# Output: training_data.csv (500 rows, 20 cols)
```
- [ ] 500+ deals in training set
- [ ] Labels balanced (70% won, 30% lost)
- [ ] No NaNs (< 5% acceptable)

**Day 22-24: Feature Engineering**
```python
# Extract 15 features:
# Stage encoding, days_in_stage, engagement_velocity,
# stakeholder_count, economic_buyer_engaged, deal_size,
# proposal_sent, days_since_proposal, competitor_mentioned, etc

# Output: features.pkl (500 rows, 15 cols)
```
- [ ] All 15 features engineered
- [ ] No missing values
- [ ] Correlation check (remove highly correlated)

**Day 25: Model Training**
```python
# Train XGBoost
# Expected AUC: 0.85+

python backend/ml/train_deal_probability.py
# Output: model_v1.0.0.pkl
```
- [ ] AUC >= 0.85 on validation
- [ ] Precision >= 80%, Recall >= 75%

**Day 26-27: Hyperparameter Tuning + Calibration**
```python
# Grid search: n_estimators, max_depth, learning_rate
# Calibrate probabilities: platt scaling
# Calculate 90% confidence intervals
```
- [ ] Final AUC 0.85-0.90
- [ ] Model properly calibrated
- [ ] CI working correctly

**Day 28-30: Model Deployment + Wrapper**
```python
# Save model: deal_probability_v1.0.0.pkl
# Create wrapper class: DealProbabilityModel
# Test predict() method with 20 deals
```
- [ ] Model saved to S3 + code repo
- [ ] Wrapper class tested
- [ ] Model version = "1.0.0"

### Deliverables (Day 30 EOD)
```
✅ Training data (500 deals)
✅ 15 features engineered
✅ XGBoost model (AUC 0.85+)
✅ Model saved + versioned
✅ Wrapper class ready for API
```

---

## SPRINT 4: API ENDPOINTS (Week 7)

### Daily Breakdown

**Day 31: Stakeholders Endpoint**
```python
# GET /api/v1/intelligence/stakeholders/{deal_id}
# Returns: buying committee + economic buyer

pytest tests/test_api.py::test_get_stakeholders_200 -v
```

**Day 32: Probability Endpoint**
```python
# GET /api/v1/intelligence/probability/{deal_id}
# Returns: close_probability + CI + confidence

pytest tests/test_api.py::test_get_probability_* -v
```

**Day 33: Health Endpoint**
```python
# GET /api/v1/intelligence/health/{deal_id}
# Returns: health_score + components + recommendations

pytest tests/test_api.py::test_get_health_* -v
```

**Day 34: Alerts Endpoints**
```python
# GET /api/v1/intelligence/alerts
# POST /api/v1/intelligence/alerts/{id}/acknowledge

pytest tests/test_api.py::test_alerts_* -v
```

**Day 35: Webhooks + Integration**
```python
# POST /api/v1/intelligence/stakeholders/{deal_id}/engagement
# Salesforce webhook handler
# Email tracking webhook handler

pytest tests/test_webhooks.py -v
```

### Deliverables (Day 35 EOD)
```
✅ 5 REST endpoints
✅ Swagger/OpenAPI docs
✅ Webhook receivers tested
✅ All endpoints < 200ms p95
```

---

## SPRINT 5: FRONTEND + TESTING (Week 8)

### Daily Breakdown

**Day 36: DealHealthCard**
```bash
# Create component: DealHealthCard.tsx
# Displays: health_score (0-100), status (healthy/at_risk/critical)
# Color-coded: green/yellow/red

npm run storybook  # Visual testing
```

**Day 37: BuyingCommitteePanel**
```bash
# Create: BuyingCommitteePanel.tsx
# Shows: stakeholders + roles + engagement scores
# Highlight economic buyer
```

**Day 38: DealProbabilityChart**
```bash
# Create: DealProbabilityChart.tsx
# Gauge chart: close_probability (0-100)
# Show: 90% CI, confidence level, trend
```

**Day 39: Alerts + Recommendations**
```bash
# Create: AlertsPanel.tsx + RecommendedActionsPanel.tsx
# List: unresolved alerts
# Actions: call economic buyer, re-engage, escalate
```

**Day 40: Dashboard Integration + UAT**
```bash
# Integrate all 4 components into DealIntelligenceDashboard
# Performance test: 100 concurrent users
# UAT with 5 power users (5-10 deals)
```

### Deliverables (Day 40 EOD)
```
✅ 4 React components
✅ Dashboard fully integrated
✅ 100 concurrent users tested
✅ UAT passed (power users)
```

---

## DAILY STAND-UP FORMAT (Async, Slack #phase-27)

**Every morning 9am UTC**, post:
```
[DAY X/40] [SPRINT Y/5] [NAME]

✅ DONE YESTERDAY
- Task 1
- Task 2

⚠️ BLOCKERS
None | [Issue + mitigation]

🎯 TODAY
- Task 1
- Task 2

📊 PROGRESS
[Health score]: X% complete
```

---

## SUCCESS CRITERIA

**Go/No-Go Checklist (Day 40)**

- [ ] All tests passing (pytest -v)
- [ ] Code coverage 80%+
- [ ] API responses < 200ms p95
- [ ] Dashboard loads < 2s
- [ ] 99%+ uptime (staging, 1 week)
- [ ] Forecast accuracy +10% (baseline)
- [ ] 5+ sales team using health scores
- [ ] UAT passed (power users)
- [ ] No P0/P1 bugs
- [ ] Documentation complete
- [ ] Team trained

**All must pass for Phase 27 Go-Live**

---

## ESCALATION PATH

**Issue Severity**:
- **P0** (blocker, prod down): Escalate immediately to engineering lead
- **P1** (high impact): Daily standup mention
- **P2** (medium): Track in sprint retro

**Escalation**: Slack #phase-27-blocked or engineering-escalations

---

## TOOLS & COMMANDS

```bash
# Daily development
pytest tests/test_deal_intelligence_manager.py -v -s
black backend/app/domains/enterprise/deal_intelligence.py
flake8 backend/app/domains/enterprise/

# Code quality
pylint backend/app/domains/enterprise/deal_intelligence.py
coverage report --fail-under=80

# Performance
python -m cProfile -s cumtime backend/benchmark.py
ab -n 100 -c 10 http://localhost:8000/api/v1/intelligence/health/deal_001

# Git workflow
git add .
git commit -m "feat: [message]"
git push origin feature/phase-27-deal-intelligence
# Create PR → code review → merge to phase-27-staging

# Deployment (end of sprint)
git checkout phase-27-staging
git pull origin main
alembic upgrade head
pytest tests/ --cov
# Ready for production
```

---

**Phase 27 Sprint Kickoff - Ready to Start Monday** ✅

