# 🔐 SellIA — Guía de Hardening para Producción

## Checklist Pre-Deploy

### 1. Claves de Cifrado

- [ ] `SECRET_KEY`: mínimo 32 caracteres aleatorios. Generar con:
  ```bash
  openssl rand -hex 32
  ```
- [ ] `FERNET_SECRET`: mínimo 32 caracteres, **diferente** de `SECRET_KEY`. Generar con:
  ```bash
  openssl rand -base64 32
  ```
  > ⚠️ Si cambiás `FERNET_SECRET` después de tener datos encriptados, **perdés el acceso a esos datos**.
- [ ] `BACKUP_ENCRYPTION_KEY`: mínimo 32 caracteres aleatorios.

### 2. Base de Datos

- [ ] `DB_PASSWORD`: contraseña larga y aleatoria (no usar `devpassword123`).
- [ ] `DB_SSL_MODE`: en producción con DB remota, usar `require`, `verify-ca` o `verify-full`.
- [ ] `DB_SSL_CA`: si usás `verify-ca` o `verify-full`, montar el certificado CA en el contenedor:
  ```yaml
  volumes:
    - ./certs/db-ca.crt:/app/certs/db-ca.crt:ro
  ```
  Y setear `DB_SSL_CA=/app/certs/db-ca.crt`.
- [ ] En Docker Compose, comentar o eliminar los puertos expuestos de `db` y `redis`:
  ```yaml
  # ports:
  #   - "5432:5432"
  ```

### 3. Nginx / Reverse Proxy

- [ ] `client_max_body_size` está alineado con el backend (10 MB general, 50 MB upload).
- [ ] Configurar HTTPS / TLS 1.3 en Nginx (descomentar puerto 443 en `docker-compose.yml`).
- [ ] Usar certificados de Let's Encrypt o Cloudflare Origin CA.
- [ ] Si usás Cloudflare:
  - Activar "Always Use HTTPS"
  - Habilitar "Authenticated Origin Pulls" (mTLS)
  - Crear Page Rule: `app.sellia.com/api/*` → Cache Level: Bypass
  - Crear Page Rule: `app.sellia.com/*` → Security Level: High

### 4. API & Aplicación

- [ ] `ENVIRONMENT=production` en `.env`.
- [ ] `ENABLE_OPENAPI=false` para ocultar `/docs` y `/redoc`.
- [ ] Verificar que `BLOCKED_COUNTRIES` tenga los códigos ISO deseados.
- [ ] Revisar que `CORS` en `main.py` solo permita el dominio de producción.

### 5. Backups

- [ ] El servicio `db-backup` corre automáticamente cada 24h.
- [ ] Los backups se encriptan con AES-256-CBC + PBKDF2 (100k iteraciones).
- [ ] Solo se mantienen los últimos 7 backups (rotación automática).
- [ ] El volumen `postgres_backups` persiste entre reinicios.

### 6. Rotación de Secretos

Celery Beat ejecuta automáticamente:
- `data_retention_cleanup` → semanal (borra datos antiguos)
- `rotate_webhook_tokens` → semanal (rota tokens de webhook > 90 días)
- `rotate_expired_secrets` → semanal (rota secrets de webhooks de seguridad)

### 7. Logs y Monitoreo

- [ ] Revisar `data_access_logs` periódicamente para detectar accesos anómalos.
- [ ] Configurar alertas en Cloudflare para rate-limiting excedido.
- [ ] Considerar activar ELK (`ELK_ENABLED=true`) para centralizar logs de seguridad.

---

## Comandos Útiles

```bash
# Verificar estado de todos los servicios
docker compose ps

# Forzar rotación de tokens manualmente
docker exec ia_vendedor_celery_worker celery -A app.tasks.celery_app call app.tasks.security_tasks.rotate_webhook_tokens

# Forzar cleanup de retención manualmente
docker exec ia_vendedor_celery_worker celery -A app.tasks.celery_app call app.tasks.security_tasks.data_retention_cleanup

# Ver logs de auditoría recientes
docker exec ia_vendedor_db psql -U ia_vendedor -d ia_vendedor -c "SELECT * FROM data_access_logs ORDER BY created_at DESC LIMIT 20;"

# Verificar que RLS está activo en tablas críticas
docker exec ia_vendedor_db psql -U ia_vendedor -d ia_vendedor -c "SELECT tablename, rowsecurity FROM pg_tables WHERE schemaname='public' AND rowsecurity=true;"
```
