# Deployment: Automation Toggles System

Production deployment checklist + scripts.

## Pre-Deployment Checklist

### Backend

- [ ] Run migrations: `alembic upgrade head`
- [ ] All tests pass: `pytest backend/tests/test_automation_toggles*.py -v`
- [ ] Middleware integrated in `app.sellbot.py`
- [ ] No `TODO` comments in toggle code
- [ ] Environment vars set (if needed)

### Frontend

- [ ] Component tests pass: `npm test -- ToggleSwitch.test.tsx`
- [ ] Build succeeds: `npm run build`
- [ ] `/sellia-brain` loads without errors
- [ ] Dark mode tested
- [ ] Mobile responsive checked

### Database

- [ ] Alembic revision: `x4y5z6a7b8c9_add_automation_toggles_tables.py` applied
- [ ] Tables exist: `automation_toggles`, `toggle_audit_logs`
- [ ] Indices created

## Deployment Steps

### Step 1: Migrate Database

```bash
# Local
alembic upgrade head

# Production (Railway)
railway run alembic upgrade head
```

### Step 2: Deploy Backend (Railway)

```bash
# Push to GitHub
git push origin main

# Railway auto-deploys from GitHub
# Check: railway logs
```

Verify:
```bash
# Test endpoints
curl https://sellia-production.up.railway.app/api/v1/automations/toggles/dashboard/test-business-id
```

### Step 3: Deploy Frontend (Vercel)

```bash
# Push to GitHub (same as backend)
git push origin main

# Vercel auto-deploys from GitHub
# Check: vercel.com dashboard
```

Verify:
```bash
# Navigate to https://sellia-brain.vercel.app/sellia-brain
# Check tabs load (Overview | Control Center | Analytics)
```

### Step 4: Verify Integration

Production E2E:

```bash
# 1. Create new business via /api/v1/businesses
POST https://sellia-production.up.railway.app/api/v1/businesses
{
  "name": "Test Company",
  "type": "ecommerce",
  "description": "Testing toggles"
}
# Response: {"id": "...", "name": "Test Company"}

# 2. List toggles (should have 12 from auto-seed)
GET https://sellia-production.up.railway.app/api/v1/automations/toggles/business/{business_id}
# Response: 12 toggles with all categories

# 3. Access frontend
# Visit https://sellia-brain.vercel.app/sellia-brain
# Switch to "Control Center" tab
# Should show 12 toggles grouped by category
```

## Rollback Plan

If issues arise:

### Backend Rollback
```bash
# Revert to previous commit
git revert <commit_id>
git push origin main

# Downgrade DB if needed
alembic downgrade -1

# Check logs
railway logs
```

### Frontend Rollback
```bash
# Vercel: auto-rollback from UI or
git revert <commit_id>
git push origin main
```

## Post-Deployment

### Monitoring

- [ ] Check Railway logs: `railway logs --follow`
- [ ] Check Vercel dashboard for build status
- [ ] Monitor API response times
- [ ] Check for 500 errors in logs

### Data Verification

```bash
# Verify DB
psql $DATABASE_URL -c "SELECT COUNT(*) FROM automation_toggles;"
# Should show hundreds of toggles (12 per business)

# Check migrations
psql $DATABASE_URL -c "SELECT * FROM alembic_version;"
# Should show x4y5z6a7b8c9 in list
```

### User Testing

1. Create test business via signup
2. Verify toggles auto-seeded in DB
3. Test Control Center UI
4. Disable a toggle
5. Verify audit log created
6. Test that disabled feature returns 403 error

## Environment Variables

Ensure these are set in Railway:

```
DATABASE_URL=postgresql://...
SECRET_KEY=...
ANTHROPIC_API_KEY=...
ALLOWED_ORIGINS=https://sellia-brain.vercel.app
```

## Alerts & SLOs

- Response time: < 500ms for toggle APIs
- Error rate: < 0.1% for toggle endpoints
- Availability: 99.9% uptime

Monitor via Railway dashboard.

## Troubleshooting

### Issue: 404 on /api/v1/automations/toggles

**Cause**: Router not included in main.py
**Fix**: Check `app.main:_try_include("app.api.v1.automations.router", ...)`

### Issue: Toggles not created on signup

**Cause**: seed_toggles_for_business() failed silently
**Fix**: Check railway logs for warnings, verify DB connection

### Issue: UI not loading

**Cause**: API request failed
**Fix**: Check Vercel build logs, verify CORS headers

### Issue: Middleware blocking all requests

**Cause**: business_id extraction failed
**Fix**: Add `X-Business-ID` header in requests

## Deployment Success Criteria

- ✅ 12 toggles created when new business created
- ✅ UI loads 3 tabs (Overview | Control Center | Analytics)
- ✅ Can toggle ON/OFF without errors
- ✅ Audit log recorded for each change
- ✅ Middleware returns 403 when disabled
- ✅ Usage counter increments on API calls
- ✅ No console errors in browser
- ✅ Dark mode works
- ✅ Mobile responsive

## Rollout Strategy

### Phase 1: Canary (5%)
- Deploy to 5% of traffic
- Monitor for 1 hour
- Check logs and errors

### Phase 2: Staging (25%)
- If Phase 1 OK, increase to 25%
- Monitor for 2 hours
- Manual testing

### Phase 3: Production (100%)
- If Phase 2 OK, full rollout
- Keep rollback ready for 24 hours

## Communication

1. Notify team before deployment
2. Post deployment status to Slack
3. Monitor for user reports
4. Send post-deployment summary

---

**Deployment Date**: [DATE]
**Deployed By**: [YOUR_NAME]
**Status**: Ready for Production ✅
