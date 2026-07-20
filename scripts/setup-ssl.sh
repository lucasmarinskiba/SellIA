#!/usr/bin/env bash
# SellIA — SSL Setup Script
# Genera certificados de Let's Encrypt para producción

set -e

DOMAIN=${1:-""}
EMAIL=${2:-""}

if [ -z "$DOMAIN" ] || [ -z "$EMAIL" ]; then
    echo "Uso: $0 <dominio> <email>"
    echo "Ejemplo: $0 app.sellia.com admin@sellia.com"
    exit 1
fi

echo "🔐 Configurando SSL para $DOMAIN..."

# Crear estructura de certbot
mkdir -p certbot/conf certbot/www certbot/logs

# Generar certificado con certbot (modo standalone, requiere puerto 80 libre)
docker run -it --rm \
    -v "$(pwd)/certbot/conf:/etc/letsencrypt" \
    -v "$(pwd)/certbot/www:/var/www/certbot" \
    -p 80:80 \
    certbot/certbot certonly \
    --standalone \
    --agree-tos \
    --no-eff-email \
    -m "$EMAIL" \
    -d "$DOMAIN" \
    -d "www.$DOMAIN"

# Crear symlinks para nginx
ln -sf "$(pwd)/certbot/conf/live/$DOMAIN/fullchain.pem" certs/fullchain.pem
ln -sf "$(pwd)/certbot/conf/live/$DOMAIN/privkey.pem" certs/privkey.pem

echo "✅ Certificados generados correctamente."
echo "   fullchain.pem -> certs/fullchain.pem"
echo "   privkey.pem   -> certs/privkey.pem"
echo ""
echo "Iniciá SellIA en producción con:"
echo "   docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d"
