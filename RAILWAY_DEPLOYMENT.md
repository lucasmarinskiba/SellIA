# Railway Deployment: Step-by-Step

**Goal:** Add env vars + run migrations to create UserMemory tables

**Time:** ~10 minutes

---

## Step 1: Add Environment Variables (3 min)

### Via Railway Web Dashboard

**URL:** https://railway.com/project/02a8ccec-e9fc-4af7-b0d5-84e4df927d2b

**Path:** Settings → Variables

### Required Variables (MUST ADD)

```
ENVIRONMENT
production

ANTHROPIC_API_KEY
sk-ant-v0-<your-key>
(Get from: https://console.anthropic.com/account/keys)

FRONTEND_URL
https://sellia-brain.vercel.app

SECRET_KEY
<generate: openssl rand -base64 32>
```

### Recommended (add if available)

```
MERCADOPAGO_ACCESS_TOKEN
APP_<token>

TURNSTILE_SECRET_KEY
0x4AAA<secret>

WEBAUTHN_RP_ID
sellia-brain.vercel.app

WEBAUTHN_RP_ORIGIN
https://sellia-brain.vercel.app
```

### Steps to Add

1. Click **Settings** (bottom left in Railway project)
2. Click **Variables** tab
3. For each variable:
   - Click **+ Add Variable**
   - Enter **Name** (e.g., ENVIRONMENT)
   - Enter **Value** (e.g., production)
   - Click **Add**
4. After all added, Railway **auto-redeploys** the SellIA service

**Verify:** You should see all variables listed with green checkmarks

---

## Step 2: Run Migrations (3 min)

After env vars are added and service redeploys.

### Method A: Railway CLI (Easiest)

```bash
railway run python backend/run_migrations.py
```

### Method B: Via Web Shell

1. Go to: https://railway.com/project/02a8ccec-e9fc-4af7-b0d5-84e4df927d2b
2. Click **SellIA** service
3. Click **Shell** tab
4. Run:
```bash
cd /app && python backend/run_migrations.py
```

### Method C: SSH

```bash
railway shell
cd /app && python backend/run_migrations.py
```

### Expected Output

```
2026-08-22 19:00:00,000 [INFO] Running Alembic migrations...
2026-08-22 19:00:15,000 [INFO] ✓ Migrations completed successfully
2026-08-22 19:00:15,000 [INFO] ✓ All done! SellIA backend is ready.
```

**Success:** Exit code 0, "Migrations completed successfully"

**Failure:** Exit code 1, error message shown. Check logs:
```bash
railway logs -f SellIA
```

---

## Step 3: Verify Migrations Applied (2 min)

### Option A: Check DB directly

```bash
# Connect to Railway PostgreSQL
railway run psql

# List tables
\dt user_memory*

# Should show:
#  public | user_memory          | table | postgres
#  public | user_memory_events   | table | postgres
#  public | user_preferences     | table | postgres
```

### Option B: Test API endpoint

```bash
# First, get auth token
TOKEN=$(curl -X POST https://sellia-production.up.railway.app/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}' \
  | jq -r '.access_token')

# Test memory endpoint
curl https://sellia-production.up.railway.app/api/v1/memory/me \
  -H "Authorization: Bearer $TOKEN"

# Should return user memory object with new columns
```

### Option C: Check logs

```bash
railway logs -f SellIA | grep -i "migrations\|table\|user_memory"
```

---

## Troubleshooting

### Migration fails: "relation already exists"

**Cause:** Tables may already exist  
**Fix:** That's OK, Alembic skips existing tables. Run migrations again.

```bash
railway run python backend/run_migrations.py
```

### Migration fails: "database connection refused"

**Cause:** DATABASE_URL not set or invalid  
**Fix:** Check Railway Variables section:
- DATABASE_URL should be auto-set by Railway
- It should start with `postgresql://` or look like `postgres://...@host:5432/db`

```bash
railway run echo $DATABASE_URL
```

### Migration fails: "no such table"

**Cause:** Partial migrations, old schema state  
**Fix:** Check existing tables and run alembic downgrade:

```bash
railway run alembic downgrade base
railway run python backend/run_migrations.py
```

### `/memory/me` endpoint returns 404

**Cause:** Migrations didn't run or didn't complete  
**Fix:** Check logs:

```bash
railway logs -f SellIA | grep -i "memory\|migration"
```

If tables don't exist:
```bash
railway run python backend/run_migrations.py
```

---

## What Gets Created

### Tables

**user_memory** (1 row per user)
- Persistent profile: language, tone, industry, interests, challenges
- Engagement scores: engagement, satisfaction, churn_risk
- Session context: last active business/conversation/agent

**user_memory_events** (many rows per user)
- Event log: message_sent, action_taken, feedback_given
- Audit trail for analytics
- Links to conversation, business, agent (nullable)

**user_preferences** (granular config)
- Key-value pairs per user
- Flexible schema for future extensions
- Unique constraint: (user_id, preference_key)

### Indexes

- `user_id` on all tables (fast user lookups)
- `event_type`, `created_at` on events (for analytics)
- `preference_key` on preferences

---

## Test After Deploy

### Unit Tests (Local)

Already passed locally:
```bash
cd backend
python test_memory_direct.py  # Model isolation test
```

### Integration Test (Against Railway DB)

After migrations, run:
```bash
DATABASE_URL="postgresql://..." python test_memory_simple.py
```

### Manual Test (cURL)

Sign up test user:
```bash
curl -X POST https://sellia-production.up.railway.app/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email":"test@example.com",
    "password":"testpass123",
    "full_name":"Test User"
  }'
```

Response:
```json
{
  "access_token": "eyJ0eXAi...",
  "user_id": "uuid",
  ...
}
```

Get memory:
```bash
curl https://sellia-production.up.railway.app/api/v1/memory/me \
  -H "Authorization: Bearer eyJ0eXAi..."
```

Response:
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "preferred_language": "es",
  "total_conversations": 0,
  "total_messages": 0,
  "key_interests": [],
  "key_challenges": [],
  ...
}
```

Update memory:
```bash
curl -X PATCH https://sellia-production.up.railway.app/api/v1/memory/me \
  -H "Authorization: Bearer ..." \
  -H "Content-Type: application/json" \
  -d '{
    "industry_focus": "ecommerce",
    "preferred_tone": "aggressive"
  }'
```

---

## Checklist

- [ ] **Env vars added** to Railway (ENVIRONMENT, ANTHROPIC_API_KEY, etc.)
- [ ] **Service redeployed** after adding vars (check SellIA status = Online)
- [ ] **Migrations run** successfully (exit code 0)
- [ ] **Tables created** (verify via DB or logs)
- [ ] **API endpoint works** (GET /api/v1/memory/me returns data)
- [ ] **Frontend deployed** (with updated NEXT_PUBLIC_API_URL=Railway URL)
- [ ] **Multi-user tested** (User A ≠ User B data)

---

## Next Steps After Deploy

1. ✅ Tables created via migrations
2. ⏳ Wire frontend to use `/api/v1/memory` endpoints
3. ⏳ Create memory dashboard UI
4. ⏳ SellIA uses memory for personalization
5. ⏳ WebSocket streaming for real-time chat
6. ⏳ Churn prediction + feature recommendations

---

**Time to deploy:** ~10 minutes  
**Time to verify:** ~5 minutes  
**Total:** ~15 minutes to full multi-user setup

Start with Step 1 👇
