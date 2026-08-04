#!/bin/bash
set -e

echo "=== SellIA Backend Deploy a Render.com ==="
echo ""

# 1. Crear render.yaml (Infrastructure as Code)
cat > backend/render.yaml <<'EOF'
services:
  - type: web
    name: selliaai-backend
    env: python
    plan: free
    buildCommand: "pip install -r requirements.txt"
    startCommand: "uvicorn app.sellbot:app --host 0.0.0.0 --port 8000"
    envVars:
      - key: DATABASE_URL
        value: sqlite+aiosqlite:///./test.db
      - key: REDIS_URL
        value: redis://localhost:6379/0
      - key: ALLOWED_ORIGINS
        value: "http://localhost:3000,https://sellia-brain.vercel.app"
      - key: ENVIRONMENT
        value: production
      - key: SENDGRID_WEBHOOK_KEY
        value: ""
    routes:
      - path: /
        destination: http://localhost:8000
EOF

echo "✓ render.yaml created"

# 2. Crear .renderignore
cat > backend/.renderignore <<'EOF'
.git
.gitignore
.venv
__pycache__
*.pyc
.pytest_cache
.env.local
test.db
EOF

echo "✓ .renderignore created"

# 3. Instrucciones para usuario
cat > RENDER_SETUP.md <<'EOF'
# Deploy a Render.com

## Pasos (Sin CLI necesario):

1. Ve a https://dashboard.render.com
2. Click "New +" → "Web Service"
3. Conecta tu GitHub repo: https://github.com/lucasmarinskiba/SellIA
4. Configura:
   - **Name**: selliaai-backend
   - **Branch**: main
   - **Root Directory**: backend
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.sellbot:app --host 0.0.0.0 --port 8000`
   - **Plan**: Free (o Starter $7/mo)
   - **Region**: North America
5. Environment Variables:
   ```
   DATABASE_URL=sqlite+aiosqlite:///./data/test.db
   ALLOWED_ORIGINS=http://localhost:3000,https://sellia-brain.vercel.app
   ENVIRONMENT=production
   ```
6. Click "Create Web Service"

## URL Backend:
`https://selliaai-backend.onrender.com`

## Update Frontend:
- Edit `frontend/.env.production`
- Set `NEXT_PUBLIC_API_URL=https://selliaai-backend.onrender.com`
- Redeploy a Vercel

## Alternativa Rápida (GitHub Actions + Render):
- Generate Render Deploy Hook (en dashboard)
- Agregar secret a GitHub: RENDER_DEPLOY_HOOK_URL
- CI/CD automático al hacer push
EOF

echo "✓ RENDER_SETUP.md created"
echo ""
echo "=== Deployment Strategies ==="
echo "1. ✅ Render.com (Free, No trial blocks)"
echo "2. ✅ Railway.app (Free tier available)"
echo "3. ✅ Heroku (Paid)"
echo "4. ❌ Fly.io (Blocked: trial expired)"
echo ""
echo "Archivo render.yaml creado en backend/"
echo "Instrucciones en RENDER_SETUP.md"
echo ""
echo "Próximo: Abrir https://dashboard.render.com y seguir pasos"
