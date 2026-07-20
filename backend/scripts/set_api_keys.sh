#!/bin/bash
# Script para configurar API keys de OpenAI/Anthropic en SellIA
# Uso: ./set_api_keys.sh sk-openai-xxxx sk-ant-yyyy

ENV_FILE="$(dirname "$0")/../.env"

if [ $# -lt 1 ]; then
    echo "Uso: $0 <OPENAI_API_KEY> [ANTHROPIC_API_KEY]"
    echo "Ejemplo: $0 sk-proj-abc123 sk-ant-xyz789"
    exit 1
fi

OPENAI_KEY="$1"
ANTHROPIC_KEY="${2:-}"

# Backup del .env
cp "$ENV_FILE" "$ENV_FILE.backup.$(date +%s)"

# Reemplazar o agregar OPENAI_API_KEY
if grep -q "^OPENAI_API_KEY=" "$ENV_FILE"; then
    sed -i "s|^OPENAI_API_KEY=.*|OPENAI_API_KEY=$OPENAI_KEY|" "$ENV_FILE"
else
    echo "OPENAI_API_KEY=$OPENAI_KEY" >> "$ENV_FILE"
fi

# Reemplazar o agregar ANTHROPIC_API_KEY
if [ -n "$ANTHROPIC_KEY" ]; then
    if grep -q "^ANTHROPIC_API_KEY=" "$ENV_FILE"; then
        sed -i "s|^ANTHROPIC_API_KEY=.*|ANTHROPIC_API_KEY=$ANTHROPIC_KEY|" "$ENV_FILE"
    else
        echo "ANTHROPIC_API_KEY=$ANTHROPIC_KEY" >> "$ENV_FILE"
    fi
fi

echo "✅ API keys actualizadas en $ENV_FILE"
echo "🔄 Reiniciando backend..."
docker restart ia_vendedor_backend 2>/dev/null || echo "Docker no disponible, reiniciá manualmente: docker restart ia_vendedor_backend"

sleep 5
echo "🩺 Verificando health check..."
curl -s http://localhost:8001/health | grep -o '"status":"[^"]*"' || echo "Health check no responde todavía, esperá 10 segundos más"
