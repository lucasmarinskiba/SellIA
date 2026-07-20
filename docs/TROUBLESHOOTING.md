# Troubleshooting Guide

## Backend

### "SECRET_KEY está usando un valor por defecto inseguro"

**Síntoma**: La app no arranca con error:
```
ValueError: SECRET_KEY está usando un valor por defecto inseguro.
```

**Causa**: `SECRET_KEY` es demasiado corta (< 32 chars) o está en la lista de defaults inseguros.

**Solución**:
```bash
# Generar nueva clave
openssl rand -hex 32

# Agregar a .env
SECRET_KEY=<el-valor-generado>
```

---

### "cannot perform operation: another operation is in progress"

**Síntoma**: Error de asyncpg en tests o requests concurrentes.

**Causa**: SQLAlchemy async session siendo usada desde múltiples tareas async sin await.

**Solución**: Asegurar que cada request use su propia sesión via `Depends(get_db)`.

---

### "You must call FastAPILimiter.init"

**Síntoma**: Error 500 en endpoints con rate limiting.

**Causa**: `FastAPILimiter.init()` no fue llamado durante el startup.

**Solución**: Verificar que Redis esté saludable y reiniciar backend:
```bash
docker compose ps redis
docker compose restart backend
```

---

### Login devuelve 500: "UnboundLocalError: verify_password"

**Síntoma**: Login falla con 500, traceback menciona `verify_password`.

**Causa**: Import local de `verify_password` dentro de un bloque condicional en auth.py.

**Solución**: Verificar que `auth.py` no tenga imports locales dentro de `if` blocks. El import debe estar a nivel de módulo.

---

### Emails no se envían

**Síntoma**: Alertas de seguridad no llegan por email.

**Causas comunes**:
1. SMTP no configurado
2. Contraseña de app incorrecta (Gmail requiere App Password)
3. Firewall bloqueando puerto 587

**Debug**:
```bash
# Verificar configuración
docker compose exec backend env | grep SMTP

# Probar conexión SMTP manualmente
docker compose exec backend python -c "
import aiosmtplib, asyncio
async def test():
    try:
        await aiosmtplib.send('test', hostname='smtp.gmail.com', port=587, start_tls=True, username='tucuenta', password='pass')
        print('OK')
    except Exception as e:
        print(f'Error: {e}')
asyncio.run(test())
"
```

---

## Frontend

### "window is not defined" en Next.js

**Síntoma**: Build falla con error de `window` o `localStorage`.

**Causa**: Código que accede a APIs del navegador se ejecuta durante SSR.

**Solución**: Usar `typeof window !== 'undefined'` o `useEffect`:
```tsx
if (typeof window !== 'undefined') {
  const token = localStorage.getItem('token')
}
```

---

### TypeError: Cannot read properties of undefined (reading 'map')

**Síntoma**: Pantalla en blanco o error en consola al cargar listas.

**Causa**: La API devolvió un objeto en vez de array, o el campo es null.

**Solución**: Usar optional chaining y valores por defecto:
```tsx
{data?.map?.(item => ...) ?? <EmptyState />}
```

---

## Docker

### "port is already allocated"

**Síntoma**: `docker compose up` falla con error de puerto.

**Solución**:
```bash
# Encontrar proceso que usa el puerto
sudo lsof -i :5432  # PostgreSQL
sudo lsof -i :6379  # Redis
sudo lsof -i :80    # Nginx

# Matar proceso o cambiar puertos en docker-compose.yml
```

---

### Backend no responde después de cambios

**Síntoma**: Cambios en código no se reflejan.

**Causa**: Docker volume no se actualizó o uvicorn no detectó cambios.

**Solución**:
```bash
# Forzar rebuild
docker compose up -d --build backend

# O reiniciar manualmente
docker compose exec backend kill -HUP 1
```

---

### PostgreSQL: "database system is starting up"

**Síntoma**: Backend no conecta a DB.

**Causa**: PostgreSQL todavía está inicializándose.

**Solución**: Esperar a que el healthcheck pase:
```bash
docker compose ps db
# Debe decir (healthy)
```

---

## ClamAV

### "ClamAV not responding"

**Síntoma**: Upload de archivos falla.

**Causa**: ClamAV está descargando signatures por primera vez.

**Solución**: Esperar 2-3 minutos o verificar:
```bash
docker compose logs clamav --tail=20
# Debe decir "SelfCheck: Database status OK."
```

---

## Rate Limiting

### "Too many requests"

**Síntoma**: Error 429 en el frontend.

**Causa**: Rate limit de Redis activado. Límites:
- Login: 5/minuto
- Register: 3/hora
- General: 100/minuto

**Solución**: Esperar el tiempo indicado en `Retry-After` header, o limpiar Redis:
```bash
docker compose exec redis redis-cli FLUSHDB
```

---

## 2FA / Backup Codes

### "Código 2FA inválido"

**Síntoma**: No puede loguear con 2FA activado.

**Causas**:
1. Reloj del dispositivo desfasado (TOTP requiere sincronización de tiempo)
2. Se usó un código de backup ya consumido
3. La app de autenticación fue configurada con el QR incorrecto

**Solución**:
1. Sincronizar hora del celular
2. Probar con un código de backup
3. Si todo falla, un admin puede desactivar 2FA desde la DB:
```sql
UPDATE users SET is_2fa_enabled = false, totp_secret = null WHERE email = 'usuario@example.com';
DELETE FROM two_fa_backup_codes WHERE user_id = '<uuid>';
```

---

## Geofencing

### Falsos positivos de geofencing

**Síntoma**: Alertas de "login inesperado" aunque el usuario está en casa.

**Causas**:
1. ISP cambia la IP a otra ciudad
2. Usuario usa VPN
3. `max_distance_km` es muy restrictivo

**Solución**: Aumentar `max_distance_km` o desactivar geofencing:
```bash
# Como admin
curl -X PUT /api/v1/security/config \
  -d '{"max_distance_km": 1000}'
```

---

## Celery

### Tareas no se ejecutan

**Síntoma**: Background jobs (emails, webhooks) no llegan.

**Debug**:
```bash
# Verificar worker está corriendo
docker compose ps celery-worker

# Ver logs
docker compose logs celery-worker --tail=50

# Ver queue en Redis
docker compose exec redis redis-cli LLEN celery
```
