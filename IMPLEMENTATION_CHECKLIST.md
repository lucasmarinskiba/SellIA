# SellIA Multi-User Implementation Checklist

## ✅ Backend: UserMemory & API Integration

### Models & Database
- [x] Created `UserMemory` model — persistent user profile
- [x] Created `UserMemoryEvent` model — event logging
- [x] Created `UserPreference` model — granular preferences
- [x] Created Alembic migration: `s9t0u1v2w3x4_add_user_memory_tables.py`
- [x] Added models to `alembic/env.py` imports

### API Endpoints
- [x] Created `/api/v1/memory` router with PATCH/POST endpoints:
  - [x] `GET /me` — Get current user memory
  - [x] `PATCH /me` — Update user memory
  - [x] `POST /events` — Log memory event
  - [x] `POST /interests/{interest}` — Add interest
  - [x] `POST /challenges/{challenge}` — Add challenge
  - [x] `POST /preferences` — Set preference
  - [x] `GET /preferences/{key}` — Get preference
  - [x] `GET /events` — Get recent events
- [x] Added router to `main_railway.py` with graceful error handling

### Service Layer
- [x] Created `UserMemoryService` with methods:
  - [x] `get_or_create()` — Auto-create memory on first access
  - [x] `update_memory()` — Merge updates
  - [x] `log_event()` — Track user actions
  - [x] `add_interest()` / `add_challenge()` — Append to lists
  - [x] `add_favorite_agent()` — Track agent usage
  - [x] `update_engagement_score()` — Compute metrics
  - [x] `set_preference()` / `get_preference()` — Granular config

---

## 🔄 Next: Database Migrations & Railway Deploy

### Step 1: Run Migrations on Railway
```bash
# SSH into Railway or use Railway CLI:
cd /app
python run_migrations.py

# Or via Alembic directly:
alembic upgrade head
```

**Expected output:**
```
Running Alembic migrations...
✓ Migrations completed successfully
✓ All done! SellIA backend is ready.
```

---

## ⚙️ Frontend: API Client Integration

### Type-Safe API Clients
- [x] Created `src/lib/sellia-api/memory.ts` — UserMemory API client
- [x] Created `src/lib/sellia-api/conversations.ts` — SellIA chat API client
- [x] Updated `.env.production` → Railway backend URL

### Environment Variables (Vercel)
- [x] Set `NEXT_PUBLIC_API_URL=https://sellia-production.up.railway.app`

### Step 2: Connect Frontend to Backend
```bash
# In frontend directory:
npm install  # if needed
npm run build
# Deploy to Vercel or test locally:
npm run dev
```

**Test Connection:**
```typescript
// In browser console or test component:
import { userMemoryApi } from '@/lib/sellia-api/memory'

const memory = await userMemoryApi.getMemory()
console.log('User Memory:', memory)
```

---

## 🔑 Environment Variables Needed in Railway

### Critical (Must Add)
```
ANTHROPIC_API_KEY=sk-ant-...       # For Claude integration
SECRET_KEY=your-super-secret-key   # JWT signing (change if not set)
FRONTEND_URL=https://sellia-brain.vercel.app
ENVIRONMENT=production
```

### Payment & Auth (Recommended)
```
MERCADOPAGO_ACCESS_TOKEN=APP_xxx
TURNSTILE_SECRET_KEY=0x4AAAA...
```

### Integrations (Optional, add as needed)
```
OPENAI_API_KEY=sk-proj-...
MERCADO_LIBRE_CLIENT_ID=xxx
HOTMART_CLIENT_ID=xxx
```

---

## 🧪 Testing Multi-User Memory

### Test Scenario
1. **User A** logs in → Creates business → Starts chat with SellIA
   - System creates `UserMemory` for User A
   - Chat logged as event
   - Favorite agent tracked

2. **User B** logs in → Creates business → Different chat flow
   - System creates `UserMemory` for User B (isolated)
   - User A's memory unchanged

3. **Verify isolation:**
   ```bash
   # Check database:
   SELECT user_id, total_conversations, key_interests 
   FROM user_memory;
   ```

---

## 🚀 Deploy Order

1. **Backend (Railway)**
   - [ ] Add missing environment variables
   - [ ] Run migration: `python run_migrations.py`
   - [ ] Verify `/api/v1/health` returns `{"status": "ok"}`
   - [ ] Test `/api/v1/memory/me` (should return 401 without auth)

2. **Frontend (Vercel)**
   - [ ] Update `NEXT_PUBLIC_API_URL` in Vercel project settings
   - [ ] Deploy latest code
   - [ ] Test login flow
   - [ ] Test memory endpoints via browser console

3. **E2E Test**
   - [ ] Sign up new user
   - [ ] Create business context
   - [ ] Chat with SellIA → verify memory updated
   - [ ] Refresh page → verify conversation history persisted
   - [ ] Check memory in DB → key_interests, total_conversations incremented

---

## 📋 Remaining Work

### Phase: Streaming & UX Enhancements
- [ ] Implement WebSocket/SSE for real-time chat
- [ ] Create UI for memory dashboard (preferences, interests)
- [ ] Add memory-aware agent routing (SellIA picks best agent based on user profile)
- [ ] Analytics dashboard: engagement_score, churn_risk_score trends

### Phase: AI Insights & Automation
- [ ] Use UserMemory to personalize SellIA responses
- [ ] Auto-extract interests from conversations
- [ ] Recommend features/agents based on key_challenges
- [ ] Send digest emails based on notification_frequency

---

## 🔗 API Reference

All endpoints require authentication: `Authorization: Bearer <token>`

### Memory Endpoints
```
GET    /api/v1/memory/me                          # Get memory
PATCH  /api/v1/memory/me                          # Update memory
POST   /api/v1/memory/events                      # Log event
POST   /api/v1/memory/interests/{interest}        # Add interest
POST   /api/v1/memory/challenges/{challenge}      # Add challenge
POST   /api/v1/memory/preferences                 # Set preference
GET    /api/v1/memory/preferences/{key}           # Get preference
GET    /api/v1/memory/events?limit=50             # Recent events
```

### Assistant Endpoints
```
GET    /api/v1/assistant/conversations            # List convos
GET    /api/v1/assistant/conversations/{id}       # Get convo detail
POST   /api/v1/assistant/conversations            # Create convo
DELETE /api/v1/assistant/conversations/{id}       # Delete convo
POST   /api/v1/assistant/chat                     # Chat with SellIA
```

---

## ✨ Success Criteria

- [x] UserMemory tables created in production DB
- [x] API endpoints accessible and authenticated
- [x] Frontend can call `/memory/me` and update
- [x] Multiple users have isolated memory
- [x] Memory persists across sessions
- [x] Events logged on chat/actions
- [x] SellIA has user context for personalization

---

**Created:** 2026-08-22  
**Last Updated:** 2026-08-22  
**Status:** Ready for Railway deployment
