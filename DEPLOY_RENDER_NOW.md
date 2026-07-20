# Deploy backend a Render — PASOS EXACTOS (lo tuyo)

Ya está todo preparado: código commiteado (git), `render.yaml`, `Dockerfile`, Render CLI instalado.
Render CLI: `C:\Users\Usuario\bin\render.exe`  (v2.19.0)

Lo que falta SÓLO lo podés hacer vos (creds + API keys + cuenta). 4 pasos:

---

## 1) Subir el repo a GitHub
El commit ya existe (sin secrets). Creá el repo y pusheá:

- Crear repo vacío: **https://github.com/new**  (nombre sugerido: `sellia`, privado)
- Luego en la terminal (en la carpeta del proyecto):
```bash
git branch -M main
git remote add origin https://github.com/<TU_USUARIO>/sellia.git
git push -u origin main
```

## 2) Crear los servicios con el Blueprint (lee render.yaml)
- Abrí: **https://dashboard.render.com/select-repo?type=blueprint**
- Conectá tu GitHub → elegí el repo `sellia` → Render detecta `render.yaml` → **Apply**.
- Crea solo: `sellia-db` (Postgres), `sellia-redis`, `sellia-api` (web Docker, health `/health`), `sellia-celery-worker`, `sellia-celery-beat`.
- `SECRET_KEY` y `FERNET_SECRET` los genera Render automáticamente.

## 3) Cargar las API keys (secrets) — sólo vos
- En el servicio **sellia-api** → pestaña **Environment**:
  - `ANTHROPIC_API_KEY` = tu key de Anthropic (provider computer-use)
  - (opcional) `OPENAI_API_KEY`, `GROQ_API_KEY`
- Link directo (tras crear): **https://dashboard.render.com** → sellia-api → Environment.
- Guardar → Render redeploya solo.

## 4) Dominio api.sellia.app
- sellia-api → **Settings → Custom Domains → Add** → `api.sellia.app`
- Render te da un **CNAME** → cargalo en el DNS de sellia.app.

---

## CLI Render (opcional, para gestionar después)
```bash
# login (abre browser, tus creds — sólo vos)
C:\Users\Usuario\bin\render.exe login

# ver servicios / disparar deploy / logs
C:\Users\Usuario\bin\render.exe services
C:\Users\Usuario\bin\render.exe deploys create <service-id>
C:\Users\Usuario\bin\render.exe logs <service-id>
```
(El alta inicial es por Blueprint en el dashboard; el CLI sirve para redeploy/logs.)

## Verificación (cuando termine, ~5-8 min)
```bash
curl https://api.sellia.app/health                 # 200
curl https://api.sellia.app/api/v1/brain/graph     # counts.total 190
```
Listo eso → `sellia-brain.vercel.app/sellia-brain` pasa de **REGISTRY SNAPSHOT** a **BACKEND LIVE**:
sinapsis reales en tiempo real + Computer Use ejecutando + dispatch real del prompt.

## (Opcional) Autodeploy en cada push
- sellia-api → Settings → **Deploy Hook** → copiar URL.
- GitHub repo → Settings → Secrets and variables → Actions → New secret:
  `RENDER_DEPLOY_HOOK_URL` = esa URL. El workflow `ci.yml` ya redeploya en push a `main`.
```
```
