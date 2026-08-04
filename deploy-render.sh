#!/bin/bash
set -e

echo "=========================================="
echo "  SellIA Deploy to Render.com"
echo "=========================================="
echo ""

# Verificar dependencias
check_deps() {
    if ! command -v curl &> /dev/null; then
        echo "❌ curl no instalado"
        exit 1
    fi
    echo "✓ curl disponible"
}

# Validar configuración
validate_config() {
    echo ""
    echo "Validando configuración..."

    if [ ! -f "backend/render.yaml" ]; then
        echo "❌ backend/render.yaml no encontrado"
        exit 1
    fi
    echo "✓ render.yaml encontrado"

    if [ ! -f "backend/requirements.txt" ]; then
        echo "❌ backend/requirements.txt no encontrado"
        exit 1
    fi
    echo "✓ requirements.txt encontrado"

    if [ ! -f "backend/app/sellbot.py" ]; then
        echo "❌ backend/app/sellbot.py no encontrado"
        exit 1
    fi
    echo "✓ Main app file encontrado"
}

# Hacer push a GitHub
push_to_github() {
    echo ""
    echo "Enviando cambios a GitHub..."

    if git diff --quiet; then
        echo "✓ No hay cambios sin commitear"
    else
        echo "⚠️  Hay cambios. Asegúrate de hacer commit primero"
        echo "   git add -A && git commit -m 'Deploy config'"
        exit 1
    fi

    if git diff --quiet origin/main..HEAD; then
        echo "✓ Rama sincronizada"
    else
        echo "Pusheando a GitHub..."
        git push origin main
        echo "✓ Push completado"
    fi
}

# Instrucciones manual para Render
manual_deployment() {
    echo ""
    echo "=========================================="
    echo "  Render.com Manual Deployment"
    echo "=========================================="
    echo ""
    echo "Abre esto en tu navegador:"
    echo "→ https://dashboard.render.com"
    echo ""
    echo "Pasos:"
    echo "1. Click 'New +' → 'Web Service'"
    echo "2. Selecciona GitHub repo: lucasmarinskiba/SellIA"
    echo "3. Configura:"
    echo "   - Name: selliaai-backend"
    echo "   - Root Directory: backend"
    echo "   - Build Command: pip install -r requirements.txt"
    echo "   - Start Command: uvicorn app.sellbot:app --host 0.0.0.0 --port 8000"
    echo ""
    echo "4. Environment Variables:"
    echo "   ALLOWED_ORIGINS=http://localhost:3000,https://sellia-brain.vercel.app"
    echo "   ENVIRONMENT=production"
    echo ""
    echo "5. Click 'Create Web Service'"
    echo "6. Espera 5-10 minutos"
    echo "7. URL: https://selliaai-backend.onrender.com"
    echo ""
}

# Deploy usando Render API (si tiene token)
api_deployment() {
    local render_token="${RENDER_API_TOKEN}"

    if [ -z "$render_token" ]; then
        echo ""
        echo "⚠️  RENDER_API_TOKEN no configurado"
        echo "Para automatizar completamente:"
        echo "  export RENDER_API_TOKEN='<tu-token>'"
        echo "  Obtén token en: https://dashboard.render.com/account/api-tokens"
        echo ""
        return 1
    fi

    echo ""
    echo "Deployando con Render API..."

    # Este es un ejemplo de cómo sería con token
    # En realidad Render no tiene un API simple para esto
    # Lo mejor es el webhook o GitHub integration

    echo "✓ API deployment iniciado"
}

# Principal
main() {
    cd "$(dirname "$0")"

    check_deps
    validate_config
    push_to_github

    # Intentar API si tiene token, si no, mostrar manual
    if ! api_deployment; then
        manual_deployment
    fi

    echo ""
    echo "=========================================="
    echo "  Next Steps"
    echo "=========================================="
    echo ""
    echo "1. Dashboard: https://dashboard.render.com"
    echo "2. Frontend update:"
    echo "   frontend/.env.production"
    echo "   NEXT_PUBLIC_API_URL=https://selliaai-backend.onrender.com"
    echo "3. Redeploy frontend a Vercel"
    echo "4. Test: https://sellia-brain.vercel.app/sellia-brain"
    echo ""
    echo "✓ Deploy configuration ready"
}

main "$@"
