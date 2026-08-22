# Railway Environment Variables Setup

## Status: Configured in Railway

Verifica en Railway (https://railway.com/project/02a8ccec-e9fc-4af7-b0d5-84e4df927d2b):

### ✅ Essential Database & Services
- [x] DATABASE_URL — PostgreSQL connection (async)
- [x] REDIS_URL — Redis cache + rate limiting

### ✅ Authentication & Security
- [x] SECRET_KEY — JWT signing key (CRITICAL: must be strong)
- [x] ALGORITHM — JWT algorithm (HS256)

### 🔄 Required for Features (Add if missing)

#### AI/LLM APIs
- [ ] ANTHROPIC_API_KEY — Claude API (for SellIA intelligence)
- [ ] OPENAI_API_KEY — GPT-4/3.5 fallback
- [ ] GROQ_API_KEY — Fast inference (free tier available)

#### Payments (MercadoPago)
- [ ] MERCADOPAGO_ACCESS_TOKEN — Production token

#### Frontend/Webhooks
- [ ] FRONTEND_URL — e.g., https://sellia-brain.vercel.app
- [ ] ENVIRONMENT — Set to "production"

#### Auth & Security
- [ ] TURNSTILE_SECRET_KEY — Cloudflare captcha (optional but recommended)
- [ ] WEBAUTHN_RP_ID — e.g., sellia-brain.vercel.app
- [ ] WEBAUTHN_RP_ORIGIN — e.g., https://sellia-brain.vercel.app

#### Integrations (Channel-specific)
- [ ] MERCADO_LIBRE_CLIENT_ID
- [ ] MERCADO_LIBRE_CLIENT_SECRET
- [ ] HOTMART_CLIENT_ID
- [ ] HOTMART_CLIENT_SECRET

#### Creator Fiscal (Optional - multi-user billing)
- [ ] CREATOR_CUIT — Tax ID
- [ ] CREATOR_CBU — Bank account
- [ ] CREATOR_MP_ALIAS — MercadoPago alias

---

## How to Add Variables to Railway

1. Go to: https://railway.com/project/02a8ccec-e9fc-4af7-b0d5-84e4df927d2b
2. Select **Environment**: Production
3. Click **Variables** tab
4. Add each variable with its value
5. Click **Deploy** to restart services

---

## Quick Checklist

```bash
# After adding vars to Railway, run migrations:
cd backend
alembic upgrade head

# Then restart:
# In Railway: redeploy the SellIA service
```

---

## Next Steps

1. ✅ Created UserMemory model & API endpoints
2. ⏳ Run migrations on Railway database
3. ⏳ Verify frontend (Vercel) connects to backend
4. ⏳ Add missing environment variables
5. ⏳ Deploy and test multi-user memory persistence
