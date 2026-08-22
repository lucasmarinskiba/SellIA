# Railway Environment Variables Setup Guide

## Quick Start

Railway URL: https://railway.com/project/02a8ccec-e9fc-4af7-b0d5-84e4df927d2b

---

## Step 1: Add Environment Variables

### Via Railway Dashboard (UI)
1. Go to: https://railway.com/project/02a8ccec-e9fc-4af7-b0d5-84e4df927d2b
2. Click **Settings** (bottom left)
3. Go to **Variables** tab
4. Click **+ Add Variable**
5. Add each var below:

### Critical Variables (Must Add)

```
ENVIRONMENT = production

ANTHROPIC_API_KEY = sk-ant-v0-<your-key-here>
    (Get from: https://console.anthropic.com/account/keys)

FRONTEND_URL = https://sellia-brain.vercel.app

SECRET_KEY = <generate-strong-random-key>
    (Example: openssl rand -base64 32)
```

### Recommended (for full features)

```
MERCADOPAGO_ACCESS_TOKEN = APP_<your-token>
    (Get from: https://www.mercadopago.com.ar/developers/panel)

TURNSTILE_SECRET_KEY = 0x4AAAA<your-secret>
    (Get from: https://dash.cloudflare.com/ → Turnstile)

WEBAUTHN_RP_ID = sellia-brain.vercel.app
WEBAUTHN_RP_ORIGIN = https://sellia-brain.vercel.app
```

### Optional (for integrations)

```
OPENAI_API_KEY = sk-proj-<your-key>
MERCADO_LIBRE_CLIENT_ID = <id>
MERCADO_LIBRE_CLIENT_SECRET = <secret>
HOTMART_CLIENT_ID = <id>
HOTMART_CLIENT_SECRET = <secret>
```

---

## Step 2: Verify Variables Added

In Railway Variables page, you should see something like:
```
✓ ENVIRONMENT = production
✓ ANTHROPIC_API_KEY = sk-ant-v0-...
✓ FRONTEND_URL = https://sellia-brain.vercel.app
✓ SECRET_KEY = ...
(and more)
```

---

## Step 3: Run Migrations

**Option A: Via Railway CLI**

```bash
railway run python backend/run_migrations.py
```

**Option B: Direct SSH to Railway**

```bash
# SSH into Railway container
railway shell

# Run migrations
cd /app && python backend/run_migrations.py
```

**Option C: Local (if DATABASE_URL is accessible)**

```bash
# Set env var locally
export DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/db"

# Run migration script
cd backend
python run_migrations.py
```

**Expected Output:**
```
[INFO] Running Alembic migrations...
[INFO] ✓ Migrations completed successfully
[INFO] ✓ All done! SellIA backend is ready.
```

---

## Step 4: Test Multi-User Memory

After migrations complete, run the test suite:

```bash
cd backend
python test_multi_user_memory.py
```

**Expected Output:**
```
[INFO] Starting Multi-User Memory Isolation Tests
[INFO] ✓ Database connection OK
[INFO] ✓ User A: <uuid>
[INFO] ✓ User B: <uuid>
[INFO] ✓ Memory A created: <uuid>
[INFO] ✓ Memory B created: <uuid>
[INFO] ✓ User A: ecommerce, growth, interests=[conversion, ads], challenges=[abandonment]
[INFO] ✓ User B: services, mature, interests=[retention, email], challenges=[scaling]
[INFO] ✓ User A: logged 3 messages
[INFO] ✓ User B: logged 2 messages
[INFO] ✓ User A memory isolated correctly
[INFO] ✓ User B memory isolated correctly
[INFO] ✓ User A data NOT in User B (isolation verified)
[INFO] ✓ User B data NOT in User A (isolation verified)

============================================================
ALL TESTS PASSED ✓
============================================================

User A:
  Industry: ecommerce
  Interests: conversion_optimization, facebook_ads
  Challenges: cart_abandonment
  Messages: 3

User B:
  Industry: professional_services
  Interests: client_retention, email_marketing
  Challenges: employee_scaling
  Messages: 2
```

---

## Step 5: Verify in Production

Check `/api/v1/memory` endpoint returns data:

```bash
# Get token from login
TOKEN=$(curl -X POST https://sellia-production.up.railway.app/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"pass"}' \
  | jq -r '.access_token')

# Get user memory
curl https://sellia-production.up.railway.app/api/v1/memory/me \
  -H "Authorization: Bearer $TOKEN"

# Response should be:
# {
#   "id": "uuid",
#   "user_id": "uuid",
#   "preferred_language": "es",
#   ...
#   "total_conversations": 0,
#   "total_messages": 0,
#   ...
# }
```

---

## Troubleshooting

### Migration fails with "relation already exists"
→ Tables may exist from old migrations. That's OK, Alembic skips them.

### `/memory/me` returns 401
→ Not authenticated. Ensure token in `Authorization: Bearer <token>` header.

### `/memory/me` returns 404 on model
→ Migrations didn't run. Check logs: `railway logs -f` on SellIA service.

### Database connection refused
→ Check `DATABASE_URL` is correct in Variables.

---

## Env Vars Checklist

Before marking complete:

- [ ] ENVIRONMENT = production
- [ ] SECRET_KEY = <strong random>
- [ ] DATABASE_URL = <set by Railway, visible>
- [ ] REDIS_URL = <set by Railway, visible>
- [ ] ANTHROPIC_API_KEY = sk-ant-...
- [ ] FRONTEND_URL = https://sellia-brain.vercel.app
- [ ] Migrations run successfully
- [ ] `test_multi_user_memory.py` passes
- [ ] API endpoint `/api/v1/memory/me` returns data

---

## Next Steps

After testing passes:

1. ✅ Environment variables configured
2. ✅ Migrations applied to production DB
3. ✅ Multi-user memory isolation verified
4. ⏳ Update frontend to use `/api/v1/memory` endpoints
5. ⏳ Add memory dashboard UI
6. ⏳ Wire up SellIA to use user memory for personalization
7. ⏳ Enable WebSocket streaming for real-time chat

---

**Status:** Ready for deployment  
**Last Updated:** 2026-08-22
