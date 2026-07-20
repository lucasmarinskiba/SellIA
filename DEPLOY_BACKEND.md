# Deploy del backend SellIA → api.sellia.app

Objetivo: que `https://sellia-brain.vercel.app/sellia-brain` tenga el **cerebro completo en vivo** (agentes, skills, automatizaciones, plataformas, sinapsis reales).

Vercel sólo hostea el frontend (Next). El backend (FastAPI + Postgres + Redis + Celery) corre aparte y se expone en `api.sellia.app`. El frontend lo consume vía rewrites de `vercel.json`.

---

## Arquitectura de red

```
Browser → sellia-brain.vercel.app
  /sellia-brain ............... Next (Command Center + NeuralGraphLive)
  /api/brain/* ................ Next route handler (snapshot bundled, Vercel-safe)
  /api/v1/* ....... rewrite →   https://api.sellia.app/api/v1/*   (FastAPI real)
  /ws/* ........... rewrite →   wss://api.sellia.app/ws/*
```

- Sin backend: NeuralGraphLive usa `/api/brain/graph` (snapshot real commiteado) → grafo completo, sinapsis en reposo.
- Con backend live: prefiere `/api/v1/brain/graph` + `/api/v1/brain/activity` → sinapsis reales.

---

## Decisión: Render (elegido)

App **stateful** (Postgres + Redis + Celery worker/beat, always-on). Render da Postgres y Redis **gestionados** (backups, sin DB ops), background workers nativos y blueprint declarativo ya completo. Fly conviene para edge/stateless global; acá pesa más la data gestionada. → **Render**. (`fly.toml` queda como alternativa).

### CI/CD automático

- **Backend**: `.github/workflows/ci.yml` job `deploy-backend` dispara Render en push a `main` (gated: corre tras tests+lint+build verdes). Requiere secret de GitHub **`RENDER_DEPLOY_HOOK_URL`** (Render → service → Settings → Deploy Hook → copiar URL). Render corre `alembic upgrade head` (preDeploy) + healthcheck.
- **Frontend**: Vercel auto-deploya en cada push a `main` (sin config extra).
- **Pre-commit hook**: `.githooks/pre-commit` regenera `brain-graph.json` (gen:brain) y lo stagea. Se activa solo tras `npm install` (script `prepare` setea `core.hooksPath .githooks`), o manual: `git config core.hooksPath .githooks`.

## Opción A — Render (recomendado, IaC con `render.yaml`)

1. Push del repo a GitHub. En `render.yaml` reemplazar `repo:` por tu URL.
2. Render → **New → Blueprint** → seleccionar el repo (rama `main`). Render lee `render.yaml` y crea:
   - `sellia-db` (Postgres 16)
   - `sellia-redis`
   - `sellia-api` (web, Docker, healthcheck `/health`)
   - `sellia-celery-worker` + `sellia-celery-beat`
3. Secrets a cargar en el dashboard (marcados `sync:false`): `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GROQ_API_KEY`. `SECRET_KEY` y `FERNET_SECRET` los genera Render.
4. Migraciones: `preDeployCommand: alembic upgrade head` (si tu plan no soporta preDeploy, correr una vez: `render exec sellia-api -- alembic upgrade head`).
5. **Dominio**: `sellia-api → Settings → Custom Domains → api.sellia.app`. Crear el CNAME que indica Render en tu DNS.
6. Verificar: `curl https://api.sellia.app/health` → `200`; `curl https://api.sellia.app/api/v1/brain/graph` → 119 nodos.

`DATABASE_URL` de Render llega como `postgres://…`; el backend lo normaliza solo a `postgresql+asyncpg://` (config.py `normalize_database_url`).

## Opción B — Fly.io (`backend/fly.toml`)

```bash
cd backend
fly launch --no-deploy
fly postgres create --name sellia-db && fly postgres attach sellia-db
fly redis create   # Upstash → set REDIS_URL
fly secrets set ENVIRONMENT=production SECRET_KEY=$(openssl rand -hex 24) \
  FERNET_SECRET=$(openssl rand -hex 24) FRONTEND_URL=https://sellia-brain.vercel.app \
  ANTHROPIC_API_KEY=...
fly deploy
fly ssh console -C "alembic upgrade head"
fly certs add api.sellia.app   # + DNS
```
Procesos `app`/`worker`/`beat` ya definidos en `fly.toml`. Región `gru` (LATAM).

## Opción C — Docker / VPS

```bash
cd backend
docker build -t sellia-api .
docker run -d -p 8000:8000 \
  -e ENVIRONMENT=production \
  -e SECRET_KEY="$(openssl rand -hex 24)" \
  -e FERNET_SECRET="$(openssl rand -hex 24)" \
  -e DATABASE_URL="postgresql+asyncpg://user:pass@db:5432/sellia" \
  -e REDIS_URL="redis://redis:6379/0" \
  -e FRONTEND_URL="https://sellia-brain.vercel.app" \
  -e ANTHROPIC_API_KEY=... \
  sellia-api
docker exec <id> alembic upgrade head
```
Reverse proxy (nginx/Caddy) TLS → `api.sellia.app` → `:8000`. Worker/beat: misma imagen con `command: celery -A app.tasks.celery_app worker|beat`.

---

## Computer Use — runtime real (que "haga miles de acciones")

El loop está **construido y verificado** (Playwright headless real: navigate/click/type/screenshot; loop de razonamiento Anthropic computer-use; política supervisado/autopilot con confirmación de acciones irreversibles **cableada**). Para que ejecute en vivo:

1. **Browsers**: el `Dockerfile` corre `playwright install --with-deps chromium`. Local: `cd backend && python -m playwright install --with-deps chromium`.
2. **API key del agente**: `ANTHROPIC_API_KEY` (provider nativo computer-use) u `OPENAI_API_KEY` (vision). Sin key → el cerebro sólo planifica (telemetría), no ejecuta.
3. **Servicios arriba**: backend + celery worker + Redis + Postgres (sesiones se persisten).
4. **Whitelist de navegación**: `COMPUTER_USE_URL_WHITELIST` (lista de dominios permitidos; vacío = todos). Seguridad: bloquea URLs fuera de la lista.
5. **Sandbox remoto (opcional)**: E2B/Browserbase para aislar el navegador fuera del contenedor. Por defecto usa Playwright local del contenedor; agregar sus keys sólo si se quiere sandbox remoto.

Verificación local del loop (sin DB ni key):
```bash
cd backend
python -m playwright install --with-deps chromium
COMPUTER_USE_URL_WHITELIST='["example.com"]' PYTHONPATH=. python scripts/cu_smoke.py   # → SMOKE OK + PNG real
pytest tests/test_autopilot_policy.py -q     # gate de irreversibles
```

**Seguridad (no se implementa, por diseño):** resolver CAPTCHA (sólo se detecta y pausa) y ejecutar operaciones financieras (trades/transferencias). Acciones irreversibles (publicar/enviar/comprar) requieren confirmación humana en modo Supervisado; las críticas (pago/credenciales) se bloquean en ambos modos.

## Variables de entorno (backend)

| Var | Requerida | Nota |
|-----|-----------|------|
| `ENVIRONMENT` | sí | `production` |
| `SECRET_KEY` | sí | ≥32 chars |
| `FERNET_SECRET` | sí | ≥32 chars |
| `DATABASE_URL` | sí | `postgres://` o `+asyncpg` (se normaliza) |
| `REDIS_URL` | sí | broker celery + cache + rate-limit |
| `FRONTEND_URL` | sí | CORS allow-origin (coma-separado) |
| `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` / `GROQ_API_KEY` | según uso | LLM |

---

## Snapshot del grafo (frontend)

`frontend/src/data/brain-graph.json` se regenera con:

```bash
cd frontend && npm run gen:brain   # corre el registry de Python si está disponible
```

Se ejecuta también en `prebuild` (antes de `next build`). Es best-effort: en Vercel (sin Python) conserva el snapshot commiteado; en local lo refresca. Tras agregar agentes/automatizaciones/plataformas al registry, correr `npm run gen:brain` y commitear el JSON.

---

## Checklist post-deploy

- [ ] `curl https://api.sellia.app/health` → 200
- [ ] `curl https://api.sellia.app/api/v1/brain/graph` → `counts.total = 119`
- [ ] `/sellia-brain` muestra badge **BACKEND LIVE** (no REGISTRY SNAPSHOT)
- [ ] Sinapsis se encienden al usar el sistema (conocimiento/tools/DB)
- [ ] Redis y Postgres conectados (logs sin errores de arranque)
