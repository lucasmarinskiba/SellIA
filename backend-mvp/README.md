# SellIA Backend MVP

Production skeleton · FastAPI + Postgres RLS + Redis + RQ + WebSockets + Alembic + pytest + CI.

## Quick start

```bash
cd backend-mvp
cp .env.example .env       # fill keys
docker-compose up -d       # postgres + redis + ollama + migrations + api + worker
```

Or local dev:
```bash
pip install -r requirements-dev.txt
docker-compose up -d postgres redis ollama
alembic upgrade head
uvicorn app.main:app --reload --port 8000 &
python -m app.jobs.worker &
```

## Layout

```
app/
├── main.py
├── core/           settings · security · logging
├── db/             SQLAlchemy 2.0 async + RLS-bound sessions
├── api/            5 routers (auth · tenants · deals · channels · billing)
├── billing/        Stripe webhook handlers
├── channels/       WhatsApp Cloud API
├── ws/             WebSocket + Redis pub/sub fanout
└── jobs/           RQ tasks + worker entrypoint
alembic/            migrations (0001_init + 0002_rls)
tests/              pytest async · conftest fixtures
.github/workflows/  3 CI workflows
```

## Multi-tenant isolation

Postgres Row-Level Security. Each session binds `app.tenant_id`. Cross-tenant queries blocked at DB layer.

## Stack

| Component | Tech |
|---|---|
| API | FastAPI 0.115 · uvicorn · ASGI |
| DB | Postgres 16 · SQLAlchemy 2 async · Alembic |
| Cache + Queue + PubSub | Redis 7 · RQ workers |
| AI | Anthropic Claude 4.7 + Ollama llama3.3 fallback |
| Billing | Stripe Subscriptions + Connect |
| Realtime | WebSocket + Redis pub/sub fanout |
| Auth | JWT (PyJWT) · bcrypt cost 12 |
| Channels | WhatsApp Cloud API (signed webhooks) |
| Tests | pytest-asyncio · httpx AsyncClient · ASGITransport |
| CI | GitHub Actions (3 workflows) |

## Endpoints

```
GET  /healthz
POST /v1/auth/signup
POST /v1/auth/login
GET  /v1/auth/me
GET  /v1/tenants/me
PATCH /v1/tenants/me
GET  /v1/deals
POST /v1/deals
PATCH /v1/deals/{id}
DELETE /v1/deals/{id}
GET  /v1/channels
POST /v1/channels
DELETE /v1/channels/{id}
POST /v1/billing/checkout
POST /v1/billing/portal
POST /webhooks/stripe
POST /webhooks/whatsapp
GET  /webhooks/whatsapp  (Meta verify handshake)
WS   /ws?token={jwt}     (subscribe tenant + user channels)
```

## Background jobs

Enqueue from anywhere:
```python
from app.jobs import enqueue
from app.jobs.tasks import generate_ai_reply
enqueue(generate_ai_reply, tenant_id, conv_id, "Cliente dice X")
```

Worker runs jobs · scheduler picks up cron-style tasks.

## WebSocket publish

```python
from app.ws import manager
await manager.publish_tenant(tenant_id, {"type": "deal_won", "amount": 1200})
await manager.publish_user(user_id, {"type": "notification", "body": "Cierre $980"})
```

Redis pub/sub fanout across N API instances.

## Tests

```bash
pytest                          # all tests
pytest tests/test_auth.py -v    # specific
pytest --cov=app                # with coverage
```

## CI/CD

- `backend-ci.yml` · ruff + mypy + pytest + coverage (40% min)
- `frontend-ci.yml` · tsc + lint + next build
- `extension-ci.yml` · manifest validate + ESLint + package zip artifact

## Migrations

```bash
alembic revision --autogenerate -m "add x"
alembic upgrade head
alembic downgrade -1
```

## Production deploy

- Hetzner CCX13 ($15/mo) or Railway · Render
- Neon / Supabase for managed Postgres
- Upstash for managed Redis
- Vercel for frontend
- Cloudflare for CDN + R2 storage
