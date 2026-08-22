# SellIA Multi-User Deployment Plan

**Status:** ✅ Code complete. Ready for Railway deployment + testing.

---

## Quick Facts

- **Backend:** UserMemory models + API endpoints ready
- **Frontend:** API clients ready (TypeScript)
- **Database:** Migration file ready
- **Testing:** Multi-user isolation tests ready
- **Documentation:** Complete setup guides included

---

## 5-Minute Deployment Plan

### Phase 1: Add Environment Variables (2 min)

**Go to:** https://railway.com/project/02a8ccec-e9fc-4af7-b0d5-84e4df927d2b/settings

Add these variables:

```
ENVIRONMENT = production
ANTHROPIC_API_KEY = sk-ant-v0-...  (from https://console.anthropic.com)
FRONTEND_URL = https://sellia-brain.vercel.app
SECRET_KEY = <generate: openssl rand -base64 32>
```

Hit Save. Railway redeploys automatically.

### Phase 2: Run Migrations (2 min)

Either:

**Option A: Local (if DATABASE_URL accessible)**
```bash
cd backend
python run_migrations.py
```

**Option B: Railway CLI**
```bash
railway run python backend/run_migrations.py
```

**Option C: SSH to Railway**
```bash
railway shell
cd /app && python backend/run_migrations.py
```

### Phase 3: Test Multi-User Isolation (1 min)

```bash
python backend/test_multi_user_memory.py
```

Expected: `✅ ALL TESTS PASSED`

---

## Files Created This Session

### Backend

| File | Purpose |
|------|---------|
| `backend/app/domains/user_memory/models.py` | UserMemory, UserMemoryEvent, UserPreference models |
| `backend/app/domains/user_memory/schemas.py` | Pydantic schemas for API |
| `backend/app/domains/user_memory/service.py` | Business logic: get_or_create, update, log_event |
| `backend/app/api/v1/user_memory.py` | FastAPI router: GET/PATCH /me, POST /events, etc. |
| `backend/alembic/versions/s9t0u1v2w3x4_add_user_memory_tables.py` | Database migration |
| `backend/run_migrations.py` | Script to run migrations on Railway |
| `backend/verify_railway_config.py` | Check env vars are set |
| `backend/test_multi_user_memory.py` | Multi-user isolation test suite |

### Frontend

| File | Purpose |
|------|---------|
| `frontend/src/lib/sellia-api/memory.ts` | Type-safe UserMemory API client |
| `frontend/src/lib/sellia-api/conversations.ts` | SellIA chat + conversation history client |
| `frontend/.env.production` | UPDATED: points to Railway backend |

### Documentation

| File | Purpose |
|------|---------|
| `IMPLEMENTATION_CHECKLIST.md` | Detailed implementation status |
| `RAILWAY_ENV_SETUP.md` | Step-by-step env var setup |
| `RAILWAY_ENV_VARS_SETUP.md` | Alternative guide with examples |
| `DEPLOY_PLAN.md` | This file |

---

## What Gets Created in DB

After migrations run, you get:

### Tables

1. **user_memory**
   - Persistent user profile
   - Preferences, interests, challenges, engagement scores
   - One row per user

2. **user_memory_events**
   - Event log: message_sent, action_taken, etc.
   - Audit trail for analytics
   - Many rows per user

3. **user_preferences**
   - Granular key-value storage
   - E.g., agent_tone_override, feature_flags
   - Extensible

### Indexes

- `user_id` (all tables) — fast user lookup
- `event_type`, `created_at` on events — for analytics queries

---

## Multi-User Isolation Guarantee

Each user's data is **completely isolated**:

```sql
-- User A's memory
SELECT * FROM user_memory WHERE user_id = 'a-uuid';

-- User B's memory (separate row)
SELECT * FROM user_memory WHERE user_id = 'b-uuid';

-- Events are partitioned by user_id
SELECT * FROM user_memory_events WHERE user_id = 'a-uuid';
```

Test verifies:
- ✓ User A data ≠ User B data
- ✓ User A interests not in User B
- ✓ User A message count separate
- ✓ Preferences isolated

---

## API Endpoints (After Deploy)

All require: `Authorization: Bearer <token>`

```bash
# Get user's memory
GET /api/v1/memory/me

# Update preferences/interests
PATCH /api/v1/memory/me
  {
    "preferred_tone": "aggressive",
    "industry_focus": "ecommerce",
    "notification_frequency": "daily"
  }

# Log an event
POST /api/v1/memory/events
  {
    "event_type": "message_sent",
    "event_data": {"topic": "conversion", "agent": "copywriter"},
    "conversation_id": "...",
    "business_id": "..."
  }

# Add interest/challenge
POST /api/v1/memory/interests/conversion_optimization
POST /api/v1/memory/challenges/cart_abandonment

# Set granular preference
POST /api/v1/memory/preferences
  {
    "preference_key": "agent_hormozi_tone",
    "preference_value": {"tone": "aggressive", "pace": "fast"}
  }

# Get recent events
GET /api/v1/memory/events?limit=50
```

---

## Verification Checklist

Before marking complete:

- [ ] All 4 env vars added to Railway
- [ ] `verify_railway_config.py` shows ✓ for critical vars
- [ ] Migrations run without errors
- [ ] `test_multi_user_memory.py` shows `ALL TESTS PASSED`
- [ ] Curl test returns memory data
- [ ] Frontend deployment links to Railway URL

---

## After Deployment

### Immediate (Phase 1)
- [ ] Add UserMemory dashboard to UI
- [ ] Wire `/memory/me` endpoint to user profile page
- [ ] Show engagement_score, interests, challenges in UI

### Near-term (Phase 2)
- [ ] SellIA uses memory to personalize responses
- [ ] Auto-extract interests from chat
- [ ] Recommend agents based on key_challenges
- [ ] Track favorite_agents automatically

### Future (Phase 3)
- [ ] WebSocket streaming for real-time chat
- [ ] Memory-based segmentation
- [ ] Predictive churn scoring
- [ ] Personalized feature recommendations

---

## Rollback (if needed)

```bash
# Undo migrations
alembic downgrade -1

# Or specific version
alembic downgrade s9t0u1v2w3x3
```

Tables get dropped. Data lost. Only do if critical error.

---

## Support Files

If you need to debug:

- **Logs:** Railway dashboard → Logs tab
- **DB access:** Railway dashboard → Database tab → Connect
- **Test locally:** Copy DATABASE_URL from Railway, run tests locally
- **Verify config:** `python verify_railway_config.py`

---

## Timeline

| Step | Time | Status |
|------|------|--------|
| Add env vars | 2 min | ⏳ Ready |
| Run migrations | 2 min | ⏳ Ready |
| Run tests | 1 min | ⏳ Ready |
| Deploy frontend | 1 min | ⏳ Ready |
| **Total** | **6 min** | ✅ **Ready** |

---

## Success Criteria

✅ = deployment successful

- ✅ Migrations ran without errors
- ✅ `test_multi_user_memory.py` passed all tests
- ✅ User A data ≠ User B data (isolation verified)
- ✅ `/api/v1/memory/me` returns user memory
- ✅ Multiple users can chat independently
- ✅ Memory persists across sessions

---

**Generated:** 2026-08-22  
**Commit:** `74a1b68`  
**Status:** ✅ Ready for production deployment
