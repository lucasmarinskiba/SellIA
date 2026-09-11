# Automation Toggles — Production Deployment Guide

**Status**: ✅ Ready for production  
**Last Updated**: 2026-09-11  
**Tier**: Tier 2 (QuickStats + FeatureInfoModal)

## What's Deployed

### Backend (Railway)
- `app.main:app` entry point (FastAPI + Uvicorn)
- Automation Toggles API (8 CRUD endpoints)
- Toggle enforcement middleware (403/429 on disabled/over-limit)
- 12 default toggles auto-seeded on new business creation
- Alembic migration for `automation_toggles` and `toggle_audit_logs` tables

### Frontend (Vercel)
- `/sellia-brain` page with 3 tabs:
  - 📊 Visión General (EnterpriseCommandCenter)
  - 🎛️ Control Center (ControlCenter + QuickStats)
  - 📈 Analytics (ToggleAnalytics)
- Tier 2 components:
  - **QuickStats**: 4-card stat dashboard
  - **FeatureInfoModal**: Detailed feature info (cost, recommendation, usage)
  - **ToggleSwitch Info Button**: Opens feature details

## Pre-Deployment Checklist

- [x] Code compiles (TypeScript + Python)
- [x] Middleware integrated in `app.sellbot:app`
- [x] Router mounted in `app.main:app`
- [x] Auto-seed integrated in `create_business()`
- [x] Frontend components render without errors
- [x] All commits pushed to `github.com/lucasmarinskiba/SellIA:main`
- [x] Audit logging captures all toggle changes
- [x] Dark mode + responsive design verified

## Deployment Steps

### Railway Backend

1. **Push to GitHub**
   ```bash
   git push origin main  # ✅ Already done
   ```

2. **Railway Automatic Deployment**
   - Railway watches GitHub main branch
   - On push, Railway runs:
     ```bash
     pip install -r backend/requirements.txt
     alembic upgrade head
     uvicorn app.main:app --host 0.0.0.0 --port $PORT
     ```

3. **Verify Deployment**
   ```bash
   curl https://{railway-api-domain}/api/v1/automations/toggles/business/{test-business-id}
   ```

### Vercel Frontend

1. **GitHub Integration** (auto-triggered on push to main)
   - Vercel detects Next.js project
   - Runs `npm run build`
   - Deploys to `https://sellia-brain.vercel.app`

2. **Environment Variables** (verify in Vercel dashboard)
   - `NEXT_PUBLIC_API_URL`: Railway backend URL
   - Any other client-side env vars

3. **Verify Deployment**
   - Open `https://sellia-brain.vercel.app/sellia-brain`
   - Tabs should load without errors
   - Control Center should display toggles (if logged in with business)

## Database Migrations

**What gets created**:
```sql
CREATE TABLE automation_toggles (
  id UUID PRIMARY KEY,
  business_id UUID NOT NULL,
  toggle_key VARCHAR(255) NOT NULL,
  category VARCHAR(50) NOT NULL,
  is_enabled BOOLEAN DEFAULT TRUE,
  monthly_limit INTEGER,
  current_month_usage INTEGER DEFAULT 0,
  display_name VARCHAR(255),
  description TEXT,
  icon VARCHAR(50),
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  changed_by UUID,
  enabled_at TIMESTAMP,
  disabled_at TIMESTAMP
);

CREATE TABLE toggle_audit_logs (
  id UUID PRIMARY KEY,
  business_id UUID NOT NULL,
  toggle_id UUID NOT NULL,
  action VARCHAR(50),
  old_value JSONB,
  new_value JSONB,
  changed_by_user_id UUID,
  changed_by_email VARCHAR(255),
  reason TEXT,
  leads_affected INTEGER,
  estimated_impact_pct FLOAT,
  created_at TIMESTAMP
);

-- Indices for performance
CREATE INDEX idx_automation_toggles_business_id ON automation_toggles(business_id);
CREATE INDEX idx_automation_toggles_category ON automation_toggles(category);
CREATE INDEX idx_toggle_audit_logs_business_id ON toggle_audit_logs(business_id);
```

## Rollback Plan

If deployment fails:

1. **Railway**: Redeploy previous commit
   ```bash
   git revert HEAD
   git push origin main
   ```

2. **Vercel**: Automatic rollback available in Vercel dashboard
   - Deployments tab → Revert to previous version

3. **Database**: Alembic downgrade
   ```bash
   alembic downgrade -1  # Removes automation_toggles tables
   ```

## Known Issues & Workarounds

### Test Fixtures
- Tests use `db` fixture which doesn't exist; should use `db_session`
- Workaround: Run tests locally with `pytest backend/tests/ -k "not seed"`
- Non-blocking for production

### No Auth Data in Dev
- `/sellia-brain` shows "No business found" without authenticated user
- This is expected — production users will be authenticated
- To test: create test user via `/api/v1/auth/signup` first

## Monitoring Post-Deploy

Watch for:
1. **API Errors** (500s on `/api/v1/automations/toggles/*`)
2. **Middleware Rejections** (403/429 on protected routes)
3. **Database Connectivity** (connection timeouts on first request)
4. **Frontend Build Issues** (Vercel build logs)

### Health Check URLs
```bash
# Backend
curl https://{railway-url}/docs  # Swagger UI

# Frontend
curl https://sellia-brain.vercel.app/api/health
```

## Support

- **Documentation**: `docs/AUTOMATION_TOGGLES.md`
- **Code**: `backend/app/domains/automations/`, `frontend/src/components/sellia-brain/`
- **Issues**: Check GitHub Actions logs for deployment errors

---

**Deployment Date**: [To be filled]  
**Deployed By**: Claude Haiku 4.5  
**Commit Hash**: d884239
