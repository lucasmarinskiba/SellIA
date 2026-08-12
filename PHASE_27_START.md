# Phase 27 - Deal Intelligence Foundation
## Kickoff Package (Aug 12, 2026)

**Status**: Ready to start  
**Duration**: 8 weeks (Aug 12 - Oct 3)  
**Team**: 1 backend + 1 ML + 1 frontend engineer  
**Expected Launch**: Sep 26, 2026

---

## 📦 DELIVERABLES COMPLETED

### Design & Architecture ✓
- [PHASE_27_ARCHITECTURE.md](PHASE_27_ARCHITECTURE.md) — Full system design
- [PHASE_27_EMAIL_AUTH.md](PHASE_27_EMAIL_AUTH.md) — Email verification + account approval system
- [PHASE_27_SPRINT_PLAN.md](PHASE_27_SPRINT_PLAN.md) — 8-week execution plan
- [PHASE_27_CODE_EXAMPLES.md](PHASE_27_CODE_EXAMPLES.md) — Production-ready code

### Backend Implementation ✓
- `backend/app/models/email_auth.py` — Email verification + approval models
- `backend/app/domains/auth/email_auth.py` — EmailAuthManager service (email verification, account approval, admin actions)
- `backend/app/api/v1/email_auth.py` — API endpoints (6 endpoints)
- `backend/migrations/versions/0032_email_auth_schema.py` — Database schema + seed email templates

### Frontend Implementation ✓
- `frontend/src/pages/verify-email.tsx` — Email verification flow
- `frontend/src/pages/signup/approval-request.tsx` — Approval request form
- `frontend/src/pages/signup/approval-status.tsx` — Approval status checker (polls every 30s)
- `frontend/src/components/Admin/ApprovalQueue.tsx` — Admin dashboard for approvals

### Infrastructure ✓
- Database: 4 new tables (email_verification_tokens, account_approvals, approval_audit_log, email_templates)
- Email templates: 4 default templates (verification, approval_requested, approval_approved, approval_rejected)
- Celery tasks: Async email sending (send_verification_email, notify_admins_approval_pending, send_approval_email, send_rejection_email)

---

## 🚀 QUICK START

### 1. Run Database Migration

```bash
cd backend
alembic upgrade head
```

This creates:
- Email verification token storage
- Account approval workflow tables
- Audit logging for approvals
- Email templates (pre-seeded)

### 2. Update User Model

Add to `backend/app/models/user.py`:

```python
email_verified: bool = Column(Boolean, default=False)
verified_at: Optional[datetime] = Column(DateTime)
account_approved: bool = Column(Boolean, default=False)
approval_status: str = Column(String(50), default="pending")
```

### 3. Configure Email Provider

In `backend/app/domains/auth/email_auth.py`, implement `send_email()`:

```python
# Choose provider: SendGrid, AWS SES, Mailgun, etc
def send_email(to_email: str, subject: str, body: str, html: bool = True) -> bool:
    # TODO: Implement with your email provider
    pass
```

### 4. Set Admin Emails

In `backend/app/domains/auth/email_auth.py`, update `get_admin_emails()`:

```python
def get_admin_emails() -> List[str]:
    return ["admin@sellia.com", "approvals@sellia.com"]  # Your admin list
```

### 5. Integrate Signup Flow

In signup endpoint, call:

```python
email_auth = EmailAuthManager(db)
email_auth.create_verification_token(user_id, email)
# User gets verification email
# After verification, redirect to approval-request page
email_auth.request_account_approval(user_id, email, full_name, company, role)
# Admin gets notification
# User checks status at /approval-status
```

---

## 📧 USER FLOW

```
1. User signs up (email + password)
   ↓
2. Verification email sent
   ↓
3. User clicks link → Email verified
   ↓
4. User fills company/role info
   ↓
5. Approval request submitted → Admin notified
   ↓
6. User checks status (polls every 30s)
   ↓
7a. Admin approves → Approval email sent → User can log in
7b. Admin rejects → Rejection email sent → User can contact support
```

---

## 🔧 MAIN PHASE 27 FEATURES

### 1. Deal Stakeholder Intelligence
- Map buying committees (6+ roles: economic_buyer, user_buyer, coach, blocker, influencer)
- Identify economic buyers automatically
- Track engagement per stakeholder (emails, calls, meetings)
- Real-time engagement scoring

**Database**: `intelligence.deal_stakeholders` (6 columns + 15 indexes)

### 2. Deal Probability Predictor
- ML model: XGBoost trained on 500+ historical deals
- Predicts close probability (0-100) with confidence intervals
- Features: days_in_stage, engagement_velocity, proposal_status, competitor_threats, etc (15 features)
- Model caching for <200ms API response

**Database**: `intelligence.deal_probability_scores` (6 columns)

### 3. Real-time Deal Health Scoring
- Health score (0-100): healthy, at_risk, critical
- Component scores: engagement, momentum, buyer health, competition
- Auto-alerts on health changes
- Recommended next-best-actions per deal

**Database**: `intelligence.deal_health_snapshots` (10 columns)
**Database**: `intelligence.deal_health_alerts` (9 columns)

---

## 📊 SUCCESS CRITERIA

**Week 2 (Aug 26)**:
- [ ] Database schema migrated
- [ ] EmailAuthManager fully tested
- [ ] Email sending works (end-to-end)
- [ ] Admin approval workflow tested
- [ ] Frontend pages load without errors

**Week 4 (Sep 9)**:
- [ ] Deal intelligence schema deployed
- [ ] ML model trained on historical data (AUC 0.85+)
- [ ] API endpoints tested (5/5 pass)
- [ ] Dashboard components built

**Week 8 (Oct 3)**:
- [ ] Phase 27 fully functional
- [ ] UAT passed with 5 power users
- [ ] Load testing: <200ms p95 on APIs
- [ ] Dashboard load time <2s
- [ ] Ready for Sep 26 production deployment

---

## 📁 FILE STRUCTURE

```
backend/
├── app/
│   ├── models/
│   │   └── email_auth.py          ← Email verification models
│   ├── domains/
│   │   └── auth/
│   │       └── email_auth.py      ← EmailAuthManager service
│   └── api/v1/
│       └── email_auth.py          ← API endpoints
├── migrations/versions/
│   └── 0032_email_auth_schema.py  ← Database migration
└── celery_app.py                  ← Celery tasks

frontend/src/
├── pages/
│   └── verify-email.tsx           ← Email verification page
└── pages/signup/
    ├── approval-request.tsx       ← Approval request form
    └── approval-status.tsx        ← Approval status checker
└── components/Admin/
    └── ApprovalQueue.tsx          ← Admin dashboard
```

---

## 🎯 PHASE 27 ROADMAP

### Week 1-2: Onboarding & Setup
- [ ] Team onboarding
- [ ] Verify development environment
- [ ] Confirm database access
- [ ] Email provider configured (SendGrid/AWS SES/etc)

### Week 3-4: Email Auth Finalization
- [ ] Auto-approval rules implemented (domain whitelist, company whitelist)
- [ ] Email template customization
- [ ] Admin notification preferences
- [ ] Integration tests (50+ scenarios)

### Week 5-6: Deal Intelligence Core
- [ ] Deal stakeholder enrichment service
- [ ] Engagement tracking pipeline
- [ ] ML model training & validation
- [ ] Prediction cache system

### Week 7-8: API & Dashboard
- [ ] All 5 REST APIs deployed
- [ ] React dashboard components
- [ ] Real-time alerts
- [ ] Pre-launch UAT & bug fixes

---

## 🔑 KEY FILES TO REVIEW

1. **Architecture**: [PHASE_27_ARCHITECTURE.md](PHASE_27_ARCHITECTURE.md)
2. **Email Auth Design**: [PHASE_27_EMAIL_AUTH.md](PHASE_27_EMAIL_AUTH.md)
3. **Backend Service**: `backend/app/domains/auth/email_auth.py` (300 lines)
4. **API Endpoints**: `backend/app/api/v1/email_auth.py` (200 lines)
5. **Database Schema**: `backend/migrations/versions/0032_email_auth_schema.py`
6. **Frontend Pages**: `frontend/src/pages/verify-email.tsx`, `approval-request.tsx`, `approval-status.tsx`

---

## ⚠️ CRITICAL DEPENDENCIES

- **PostgreSQL**: Must support UUID, JSONB, full-text search
- **Redis**: For caching (optional but recommended for ML predictions)
- **Celery + RabbitMQ/Redis**: For async email sending
- **Email Provider**: SendGrid/AWS SES/Mailgun API credentials
- **Claude API**: For Phase 28 (proposal generation) — not needed for Phase 27

---

## 📝 NOTES

**Email Sending**: Currently mocked in `send_email()`. Replace with actual provider before launch.

**Auto-Approval**: Placeholder in `_check_auto_approval()`. Implement rules (whitelist domains, company list, etc).

**Admin Setup**: Create admin user accounts and update `get_admin_emails()` before UAT.

**Load Testing**: Before Sep 26 launch, test with 100+ concurrent users on dashboard.

---

## 🚦 GO/NO-GO GATES

**Before proceeding to Phase 28**:
- ✓ All success criteria met
- ✓ UAT completed (5+ power users)
- ✓ Email delivery working 100%
- ✓ Zero P0 bugs
- ✓ Admin approval workflow fully functional
- ✓ Dashboard performance <2s load time

---

**Status**: Phase 27 ready to kickoff Aug 12.  
**Next Milestone**: Sep 26 production deployment.
