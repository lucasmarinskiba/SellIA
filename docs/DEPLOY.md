# Guía de Deploy a Producción

## Checklist Pre-Deploy

Antes de hacer deploy, verificar cada ítem:

### 🔐 Seguridad Crítica

- [ ] `SECRET_KEY` tiene al menos 32 caracteres y es única
- [ ] `DATABASE_URL` no contiene contraseñas por defecto
- [ ] `ENVIRONMENT=production`
- [ ] `ENABLE_OPENAPI=false` (deshabilita docs públicos)
- [ ] Cloudflare Turnstile configurado (`TURNSTILE_SECRET_KEY`)
- [ ] VAPID keys generadas (`VAPID_PRIVATE_KEY`, `VAPID_PUBLIC_KEY`)
- [ ] SMTP configurado (`SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD`)
- [ ] Redis no expuesto al público (puerto 6379 solo interno)
- [ ] PostgreSQL no expuesto al público (puerto 5432 solo interno)

### 🌍 Geofencing & Países

- [ ] `max_distance_km` configurado en SecurityConfig (ej: 500)
- [ ] `blocked_countries` actualizado según necesidad
- [ ] `alert_on_geofence` activado

### 📧 Notificaciones

- [ ] Webhooks de seguridad configurados (opcional)
- [ ] Push notifications VAPID funcionando
- [ ] Emails de alerta configurados

### 🔍 Monitoreo

- [ ] HIBP API key configurada (opcional pero recomendado)
- [ ] `alert_on_breach` activado

---

## Deploy con Docker Compose

### 1. Preparar el servidor

Requisitos mínimos:
- Ubuntu 22.04 LTS o similar
- 2 vCPU, 4GB RAM, 20GB SSD
- Docker y Docker Compose instalados

```bash
# Instalar Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker
```

### 2. Clonar y configurar

```bash
git clone <tu-repo> sellia
cd sellia

# Copiar y editar variables
cp .env.example .env
nano .env
```

Variables obligatorias:

```env
# Base de datos (usar contraseña fuerte)
DB_USER=sellia_prod
DB_PASSWORD=<GENERAR_CONTRASEÑA_FUERTE>
DB_NAME=sellia_prod

# Seguridad (GENERAR NUEVA)
SECRET_KEY=<openssl rand -hex 32>

# Entorno
ENVIRONMENT=production
ENABLE_OPENAPI=false

# Turnstile (obligatorio en producción)
TURNSTILE_SECRET_KEY=<de Cloudflare>

# VAPID para push notifications
VAPID_PRIVATE_KEY=<generar con openssl>
VAPID_PUBLIC_KEY=<correspondiente>

# SMTP para emails de alerta
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=alerts@tusitio.com
SMTP_PASSWORD=<app-password>

# API keys de IA (opcional)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

### 3. Generar VAPID keys

```bash
# En tu máquina local o servidor
openssl ecparam -genkey -name prime256v1 -noout -out vapid_private.pem
openssl ec -in vapid_private.pem -pubout -out vapid_public.pem

# Extraer valores para .env
cat vapid_private.pem | base64 -w 0  # VAPID_PRIVATE_KEY
cat vapid_public.pem | base64 -w 0   # VAPID_PUBLIC_KEY
```

### 4. Configurar Nginx + SSL

Usar [Certbot](https://certbot.eff.org/) para SSL gratuito:

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d tusitio.com -d www.tusitio.com
```

Actualizar `nginx/nginx.conf` para producción:

```nginx
upstream backend {
    server backend:8000;
}

upstream frontend {
    server frontend:3000;
}

server {
    listen 80;
    server_name tusitio.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name tusitio.com;

    ssl_certificate /etc/letsencrypt/live/tusitio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/tusitio.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # API
    location /api/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts para SSE/WebSockets
        proxy_read_timeout 86400;
        proxy_send_timeout 86400;
    }

    # Health check
    location /health {
        proxy_pass http://backend;
    }
}
```

### 5. Deploy

```bash
# Pull de imágenes y build
docker compose -f docker-compose.yml pull
docker compose -f docker-compose.yml build

# Iniciar servicios
docker compose up -d

# Verificar estado
docker compose ps
docker compose logs -f backend
```

### 6. Inicializar base de datos

```bash
# Crear tablas y migraciones
docker compose exec backend python init_db.py

# Seed de datos de prueba (solo si querés demo data)
docker compose exec backend python seed_data.py
```

### 7. Verificar post-deploy

```bash
# Health check
curl -s https://tusitio.com/health

# Login funciona
curl -X POST https://tusitio.com/api/v1/auth/login \
  -H "X-Turnstile-Token: <token>" \
  -d "username=demo@selia.com&password=DemoPassword123!"

# Headers de seguridad presentes
curl -I https://tusitio.com/api/v1/auth/login | grep -E "X-Frame|X-Content|Strict-Transport"
```

---

## Actualizaciones

### Zero-downtime deploy

```bash
# 1. Build nueva imagen
docker compose build backend

# 2. Iniciar nuevo container
docker compose up -d --no-deps --scale backend=2 backend

# 3. Verificar nuevo container saludable
sleep 10
docker compose ps

# 4. Remover container viejo
docker compose up -d --no-deps --scale backend=1 backend
```

### Backup de base de datos

```bash
# Backup automático diario con cron
0 3 * * * docker compose exec -T db pg_dump -U sellia_prod sellia_prod > /backups/sellia_$(date +\%Y\%m\%d).sql

# Backup manual
docker compose exec db pg_dump -U sellia_prod sellia_prod > backup.sql
```

---

## Deploy en AWS con Terraform + Helm

Para despliegues en producción a gran escala, usar Terraform + Kubernetes (EKS).

### 1. Infraestructura con Terraform

Ver [TERRAFORM.md](TERRAFORM.md) para detalles completos.

```bash
cd infra/terraform

# Preparar backend S3 + DynamoDB
aws s3 mb s3://sellia-terraform-state
aws dynamodb create-table \
  --table-name sellia-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

# Deploy
terraform init
terraform apply -var="db_password=$(openssl rand -base64 32)" \
  -var="acm_certificate_arn=arn:aws:acm:us-east-1:..." \
  -var="acm_certificate_arn_cloudfront=arn:aws:acm:us-east-1:..."
```

### 2. Aplicación con Helm

```bash
# Configurar kubectl
aws eks update-kubeconfig --region us-east-1 --name sellia-cluster

# Instalar SellIA
helm dependency update infra/helm/sellia
helm upgrade --install sellia infra/helm/sellia \
  --namespace sellia --create-namespace \
  --values infra/helm/sellia/values.yaml \
  --values infra/helm/sellia/values-production.yaml \
  --set secrets.secretKey="$(openssl rand -hex 32)" \
  --set secrets.databaseUrl="postgresql://..." \
  --set secrets.redisUrl="redis://..."

# Verificar
kubectl get pods -n sellia
kubectl get svc -n sellia
kubectl get ingress -n sellia
```

### 3. Monitoreo con Prometheus + Grafana

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace \
  --values infra/helm/monitoring/prometheus-values.yaml

# Port-forward a Grafana
kubectl port-forward svc/monitoring-grafana 3000:80 -n monitoring
# Login: admin / (ver valores de Helm)
```

Dashboards incluidos:
- **SellIA Security**: Logins, failed logins, geofence violations, rate limiting
- **SellIA Performance**: Latencia P99, CPU/memory, error rate

---

## Cloudflare (Recomendado)

Para máxima seguridad, poner Cloudflare delante de Nginx:

1. Cambiar DNS a Cloudflare
2. Activar **Proxy** (naranja) en los registros A/AAAA
3. Configurar en Nginx:

```nginx
# Validar que requests vengan de Cloudflare
set_real_ip_from 173.245.48.0/20;
set_real_ip_from 103.21.244.0/22;
# ... (ver Cloudflare IP ranges)
real_ip_header CF-Connecting-IP;
```

4. Configurar firewall en Cloudflare:
   - Rate limiting: 30 req/min por IP
   - Bot Fight Mode: ON
   - Security Level: High

---

## Rollback

Si algo falla:

```bash
# Ver logs del error
docker compose logs backend --tail=100

# Rollback a versión anterior
git checkout <version-anterior>
docker compose up -d --build

# Restore DB si es necesario
docker compose exec -T db psql -U sellia_prod < backup.sql
```
