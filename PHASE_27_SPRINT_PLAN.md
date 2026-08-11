# Phase 27 - Detailed Sprint Plan (8 Weeks)

---

## SPRINT 1: FOUNDATION & SCHEMA (Week 1-2)

### Sprint Goals
- Database schema designed + deployed
- ORM models created
- Data migration strategy defined
- Integration points mapped

### Day-by-Day Tasks

#### Week 1

**Day 1: Schema Design + Review**
- [ ] Create `intelligence.sql` migration file (6 tables)
- [ ] Review with backend lead (check for N+1 queries, indexes)
- [ ] Validate foreign keys + constraints
- [ ] **Deliverable**: PR with schema (ready to merge)

**Day 2: Alembic Migration**
- [ ] Create Alembic migration: `alembic/versions/0031_intelligence_schema.py`
- [ ] Test upgrade path on local DB
- [ ] Test downgrade path
- [ ] Add to pre-deployment checklist
- [ ] **Deliverable**: Migration tested end-to-end

**Day 3: ORM Models**
- [ ] Create `backend/app/models/intelligence.py` (6 SQLAlchemy models)
  - DealStakeholder
  - DealProbabilityScore
  - DealHealthSnapshot
  - DealHealthAlert
  - StakeholderEngagementEvent
  - ModelPredictionsCache
- [ ] Add relationships (FK constraints)
- [ ] Add indexes via `__table_args__`
- [ ] **Deliverable**: Models with docstrings

**Day 4: Test Data + Fixtures**
- [ ] Create `tests/fixtures/intelligence_fixtures.py` (sample deals + stakeholders)
- [ ] Write 5 unit tests (CRUD operations per model)
- [ ] Test constraint violations (should fail cleanly)
- [ ] **Deliverable**: 5/5 tests passing

**Day 5: Integration Review**
- [ ] Map integration points (Salesforce, email tracking, LinkedIn)
- [ ] Define webhook schemas (request/response)
- [ ] Update API specification
- [ ] **Deliverable**: Integration spec document

#### Week 2

**Day 6: Stakeholder Enrichment**
- [ ] Add logic to hydrate new stakeholders from Salesforce
- [ ] Fetch title, email, company from CRM
- [ ] Write enrichment service
- [ ] **Deliverable**: `StakeholderEnrichmentService` class

**Day 7: Engagement Event Ingestion**
- [ ] Design webhook receiver for email tracking
- [ ] Build envelope validation (signature check)
- [ ] Parse event payload (email_open, email_click)
- [ ] Test with sample payloads
- [ ] **Deliverable**: Webhook receiver tested

**Day 8: Deal Health Snapshot Baseline**
- [ ] Write script to calculate baseline health for all deals
- [ ] Insert first snapshot per deal
- [ ] Validate distribution (should be wide range)
- [ ] **Deliverable**: All deals have baseline health

**Day 9: Documentation**
- [ ] Schema documentation (table purposes, relationships)
- [ ] API spec (5 endpoints, request/response)
- [ ] Integration guide (Salesforce, email tracking)
- [ ] **Deliverable**: Wiki page + README

**Day 10: Sprint Review + Planning**
- [ ] Demo schema to product
- [ ] Gather feedback
- [ ] Plan Sprint 2 (backend core logic)
- [ ] **Deliverable**: Sprint 2 kickoff

---

## SPRINT 2: BACKEND CORE LOGIC (Week 3-4)

### Sprint Goals
- DealIntelligenceManager fully implemented (400 lines)
- Stakeholder intelligence working (mapping + engagement)
- Deal health scoring complete
- Unit tests 80%+ coverage

### Implementation Details

#### Week 3

**Day 11: Stakeholder Intelligence**
- [ ] Implement `get_buying_committee(deal_id)` 
- [ ] Implement `identify_economic_buyer(deal_id)`
- [ ] Implement `_calculate_engagement_score()`
- [ ] Test with 5 deals (various committee sizes)
- [ ] **Deliverable**: Stakeholder methods passing 100% of tests

**Day 12: Engagement Tracking**
- [ ] Implement `update_stakeholder_engagement()` (records events)
- [ ] Implement `_get_engagement_points()` (scoring per event type)
- [ ] Build engagement event processor
- [ ] Test email_open, call, meeting events
- [ ] **Deliverable**: Event ingestion pipeline tested

**Day 13: Deal Health Scoring - Part 1**
- [ ] Implement `calculate_deal_health()` (orchestrator)
- [ ] Implement `_score_engagement()` (0-100)
- [ ] Implement `_score_momentum()` (activity velocity)
- [ ] Implement `_score_buyer_completeness()` (committee quality)
- [ ] **Deliverable**: 4/5 scoring functions complete

**Day 14: Deal Health Scoring - Part 2**
- [ ] Implement `_score_competition()` (competitive threat)
- [ ] Implement `_generate_recommendations()` (next-best-actions)
- [ ] Implement alert creation logic
- [ ] Test 10 deals (various health scenarios)
- [ ] **Deliverable**: Deal health fully working

**Day 15: Error Handling + Validation**
- [ ] Add error handling (missing deals, invalid events)
- [ ] Add input validation (deal_id, person_id format)
- [ ] Test edge cases (empty buying committee, zero engagement)
- [ ] **Deliverable**: Robust error handling

#### Week 4

**Day 16: Unit Tests**
- [ ] Write 30+ unit tests for DealIntelligenceManager
- [ ] Test each method in isolation
- [ ] Mock database calls
- [ ] Achieve 80%+ code coverage
- [ ] **Deliverable**: Coverage report + passing tests

**Day 17: Integration Tests**
- [ ] Test end-to-end flow (engagement event → health recalc)
- [ ] Use test database (transaction rollback)
- [ ] Test 5+ scenarios (various deal states)
- [ ] **Deliverable**: Integration tests passing

**Day 18: Performance Optimization**
- [ ] Profile slow queries (N+1 problems)
- [ ] Add query result caching (Redis)
- [ ] Batch operations (health recalc all deals)
- [ ] Test with 100+ open deals
- [ ] **Deliverable**: Health calc < 500ms per deal

**Day 19: Caching Layer**
- [ ] Implement Redis cache for predictions
- [ ] Cache invalidation on engagement event
- [ ] Test cache hits (should be 90%+)
- [ ] Fallback to re-compute if cache miss
- [ ] **Deliverable**: Caching layer working

**Day 20: Sprint Review**
- [ ] Demo DealIntelligenceManager to team
- [ ] Share test coverage report
- [ ] Get approval for API spec
- [ ] Plan Sprint 3 (ML model training)
- [ ] **Deliverable**: Code review passed, ready to merge

---

## SPRINT 3: ML MODEL TRAINING (Week 5-6)

### Sprint Goals
- Training data prepared (2-year deal history)
- Features engineered (15 features)
- Model trained + evaluated (AUC 0.85+)
- Model serialized + versioned

### Implementation Details

#### Week 5

**Day 21: Data Preparation**
- [ ] Query historical deals (closed/won/lost, past 24 months)
- [ ] Should have 500-1000 deals minimum
- [ ] Calculate label: closed within 90 days = 1, else = 0
- [ ] Handle imbalanced data (70% won, 30% lost)
- [ ] **Deliverable**: Clean CSV with labels

**Day 22: Feature Engineering - Part 1**
- [ ] Stage encoding (prospect → 1, ... → 6)
- [ ] Days in stage (stage_changed_at → days)
- [ ] Days in pipeline (created_at → days)
- [ ] Engagement velocity (events/day, last 14 days)
- [ ] **Deliverable**: 4/15 features calculated

**Day 23: Feature Engineering - Part 2**
- [ ] Stakeholder features (count, avg engagement, economic buyer)
- [ ] Deal size segmentation (small/mid/enterprise)
- [ ] Proposal features (sent?, days since)
- [ ] Competition features (mentioned?, stage)
- [ ] **Deliverable**: All 15 features in DataFrame

**Day 24: Feature Validation**
- [ ] Check for NaN/missing values (should be < 5%)
- [ ] Check for outliers (days_in_stage shouldn't be > 999)
- [ ] Correlation analysis (remove correlated features)
- [ ] Feature importance ranking (tree-based)
- [ ] **Deliverable**: Feature analysis document

**Day 25: Model Training Baseline**
- [ ] Train XGBoost with default parameters
- [ ] Calculate AUC on validation set
- [ ] Generate confusion matrix + precision/recall
- [ ] If AUC < 0.80, investigate feature engineering
- [ ] **Deliverable**: Baseline model metrics

#### Week 6

**Day 26: Hyperparameter Tuning**
- [ ] Grid search over: n_estimators, max_depth, learning_rate
- [ ] 5-fold cross-validation per set
- [ ] Track best params
- [ ] Expected: AUC 0.85-0.90
- [ ] **Deliverable**: Best model found

**Day 27: Calibration + Uncertainty**
- [ ] Calibrate model probabilities (platt scaling)
- [ ] Calculate prediction intervals (90% CI)
- [ ] Test: 75% confidence deals should have higher AUC
- [ ] **Deliverable**: Calibrated model with CI

**Day 28: Feature Importance Analysis**
- [ ] Rank features by SHAP importance
- [ ] Document interpretation (which features drive close probability?)
- [ ] Remove low-importance features (< 1%)
- [ ] Re-train if feature count drops > 20%
- [ ] **Deliverable**: Feature importance report

**Day 29: Model Serialization**
- [ ] Save model to pickle + joblib
- [ ] Save feature names (for prediction)
- [ ] Version model: `deal_probability_v1.0.0.pkl`
- [ ] Store in S3 + code repo (backup)
- [ ] **Deliverable**: Model + metadata in S3

**Day 30: Model Wrapper Class**
- [ ] Create `DealProbabilityModel` class (prediction interface)
- [ ] Test `predict()` method with 20 deals
- [ ] Verify output shape + probability bounds (0-100)
- [ ] Add logging + error handling
- [ ] **Deliverable**: Model class ready for API integration

---

## SPRINT 4: API + INTEGRATION (Week 7)

### Sprint Goals
- All 5 API endpoints implemented + tested
- Salesforce sync integration
- Email tracking webhook receiver
- Celery tasks for background jobs

### Implementation Details

#### Days 31-35

**Day 31: API Endpoint - Stakeholders**
- [ ] `GET /api/v1/intelligence/stakeholders/{deal_id}`
- [ ] Returns buying committee + economic buyer
- [ ] Test with 3 deals (different committee sizes)
- [ ] Add to Swagger docs
- [ ] **Deliverable**: Endpoint live on staging

**Day 32: API Endpoint - Probability**
- [ ] `GET /api/v1/intelligence/probability/{deal_id}`
- [ ] Call ML model, return prediction + CI
- [ ] Cache for 6 hours
- [ ] Test with 5 deals (various stages)
- [ ] **Deliverable**: Endpoint live + cached

**Day 33: API Endpoint - Health**
- [ ] `GET /api/v1/intelligence/health/{deal_id}`
- [ ] Full deal health score + components
- [ ] Return recommendations
- [ ] Test with 10 deals
- [ ] **Deliverable**: Endpoint live

**Day 34: API Endpoint - Alerts**
- [ ] `GET /api/v1/intelligence/alerts` (list)
- [ ] `POST /api/v1/intelligence/alerts/{id}/acknowledge` (update)
- [ ] Filter by status (unresolved, all)
- [ ] Test alert creation + acknowledgment
- [ ] **Deliverable**: Alerts fully working

**Day 35: Engagement Recording + Webhooks**
- [ ] `POST /api/v1/intelligence/stakeholders/{deal_id}/engagement`
- [ ] Salesforce webhook handler (deal stage change)
- [ ] Email tracking webhook handler (open/click)
- [ ] Signature validation for webhooks
- [ ] Test with sample payloads
- [ ] **Deliverable**: All webhooks receiving + processing

---

## SPRINT 5: FRONTEND + TESTING (Week 8)

### Sprint Goals
- 4 React components built + integrated
- End-to-end testing (5 scenarios)
- Performance testing (100 concurrent users)
- UAT with 5-10 power users

### Implementation Details

#### Days 36-40

**Day 36: Deal Health Card Component**
- [ ] `DealHealthCard.tsx` (displays health score 0-100)
- [ ] Visual design: color-coded status (green/yellow/red)
- [ ] Shows component breakdown (engagement, momentum, etc)
- [ ] Real-time update on interval
- [ ] **Deliverable**: Component in Storybook

**Day 37: Buying Committee Panel**
- [ ] `BuyingCommitteePanel.tsx` (lists stakeholders)
- [ ] Shows roles, engagement scores, activity timeline
- [ ] Highlight economic buyer
- [ ] Click to expand details
- [ ] **Deliverable**: Component integrated

**Day 38: Deal Probability Chart**
- [ ] `DealProbabilityChart.tsx` (visualization)
- [ ] Show close probability + 90% CI
- [ ] Gauge chart (0-100 scale)
- [ ] Trend over time (last 30 days)
- [ ] **Deliverable**: Chart rendering correctly

**Day 39: Alerts + Recommendations**
- [ ] `AlertsPanel.tsx` (unresolved alerts)
- [ ] `RecommendedActionsPanel.tsx` (next-best-actions)
- [ ] Dismiss/acknowledge alerts
- [ ] Click to execute action (e.g., "Call economic buyer")
- [ ] **Deliverable**: Both panels working

**Day 40: Dashboard Integration + Testing**
- [ ] Integrate all 4 components into dashboard
- [ ] End-to-end test: Load deal → see all intelligence
- [ ] Performance test: 100 concurrent users (should be < 2s load)
- [ ] UAT with 5 power users (get feedback)
- [ ] **Deliverable**: Dashboard live on staging, UAT passed

---

## TESTING STRATEGY

### Unit Tests (Sprint 2)
```python
# 30+ tests in test_deal_intelligence_manager.py
- test_get_buying_committee()
- test_identify_economic_buyer_c_level()
- test_identify_economic_buyer_already_marked()
- test_calculate_engagement_score_new_stakeholder()
- test_calculate_engagement_score_recent_activity()
- test_calculate_deal_health_healthy()
- test_calculate_deal_health_critical()
- test_generate_recommendations_missing_buyer()
- test_alert_creation_on_health_drop()
- ... (18 more)
```

### Integration Tests (Sprint 2)
```python
# test_deal_intelligence_integration.py
- test_engagement_event_to_health_recalc()
- test_stakeholder_engagement_updates_score()
- test_email_open_event_recorded()
- test_meeting_event_updates_momentum()
- test_multiple_stakeholder_engagement()
```

### ML Model Tests (Sprint 3)
```python
# test_deal_probability_model.py
- test_model_loading()
- test_prediction_output_shape()
- test_prediction_bounds_0_100()
- test_confidence_matches_calibration()
- test_feature_names_correct()
```

### API Tests (Sprint 4)
```python
# test_deal_intelligence_api.py
- test_get_stakeholders_200()
- test_get_probability_cached()
- test_get_health_200()
- test_alerts_list_unresolved()
- test_acknowledge_alert_200()
- test_engagement_webhook_recorded()
- test_salesforce_webhook_processed()
```

### E2E Tests (Sprint 5)
```
Scenario 1: New deal created → Stage progressed → Health calculated
Scenario 2: Stakeholder added → Engagement events → Score updated
Scenario 3: Email opens tracked → Velocity increases → Probability updates
Scenario 4: Health drops → Alert created → User acknowledges
Scenario 5: Economic buyer not engaged → Recommendation "Call CFO" → User acts
```

### Performance Tests (Sprint 5)
```bash
# Load test: 100 concurrent users querying dashboard
wrk -t4 -c100 -d30s \
  https://staging/api/v1/intelligence/health/deal_001

# Expected: p95 latency < 200ms
```

---

## SUCCESS CRITERIA (PHASE 27 GO/NO-GO)

### Technical ✅
- [x] 6 database tables created + indexed
- [x] DealIntelligenceManager 400 lines, 80%+ test coverage
- [x] ML model AUC 0.85+ on validation
- [x] All 5 API endpoints < 200ms p95 latency
- [x] Dashboard loads < 2 seconds
- [x] 99.5% uptime (1 week on staging)
- [x] Celery tasks health-checking every hour

### Product ✅
- [x] Forecast accuracy +10% baseline
- [x] 5+ sales team members using health scores
- [x] 2+ deals had improved outcomes (documented)
- [x] User satisfaction 4.0+/5.0 (5-user survey)
- [x] No P0/P1 bugs on staging

### Operational ✅
- [x] All code reviewed + merged to main
- [x] Documentation complete (schema, API, components)
- [x] Team trained (30-min walkthrough)
- [x] Monitoring + alerting in place
- [x] Rollback plan defined

---

**Phase 27 Sprint Plan Complete** 🚀

Start Week 1 Monday.

