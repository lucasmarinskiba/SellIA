# Arquitectura de Seguridad SellIA

## Visión General

SellIA implementa **Defense in Depth** con 7+ capas de seguridad, desde la infraestructura hasta la capa de aplicación.

```
┌─────────────────────────────────────────────────────────────┐
│  Capa 7: Aplicación (FastAPI + Next.js)                     │
│  - Auth JWT + Sesiones DB                                   │
│  - 2FA TOTP + Backup Codes                                  │
│  - Honeypot anti-bot                                        │
│  - Rate limiting por endpoint                               │
├─────────────────────────────────────────────────────────────┤
│  Capa 6: API Gateway (Nginx + Cloudflare)                   │
│  - SSL/TLS termination                                      │
│  - WAF rules                                                │
│  - IP reputation                                            │
├─────────────────────────────────────────────────────────────┤
│  Capa 5: Middleware de Seguridad                            │
│  - Threat Intel (VPN, Tor, MITM)                            │
│  - Security headers (CSP, HSTS)                             │
│  - Audit logging                                            │
│  - Country blocking                                         │
├─────────────────────────────────────────────────────────────┤
│  Capa 4: Validación de Input                                │
│  - Turnstile CAPTCHA                                        │
│  - Strong password validation                               │
│  - SQLi/XSS detection                                       │
│  - File upload scanning (ClamAV)                            │
├─────────────────────────────────────────────────────────────┤
│  Capa 3: Protección de Datos                                │
│  - bcrypt password hashing                                  │
│  - httpOnly + Secure cookies                                │
│  - Session revocation                                       │
├─────────────────────────────────────────────────────────────┤
│  Capa 2: Monitoreo & Alertas                                │
│  - HIBP breach detection                                    │
│  - Geofencing                                               │
│  - New device alerts                                        │
│  - Push + Email + Webhook notifications                     │
├─────────────────────────────────────────────────────────────┤
│  Capa 1: Infraestructura                                    │
│  - Docker network isolation                                 │
│  - PostgreSQL + Redis ACLs                                  │
│  - Secret management (.env)                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Flujo de Autenticación

```
Usuario ──► POST /auth/login
                │
                ▼
        ┌───────────────┐
        │ Turnstile     │ ──► ¿Bot? ──► ❌ Rechazar
        │ Validation    │
        └───────────────┘
                │
                ▼
        ┌───────────────┐
        │ Rate Limit    │ ──► ¿Excedido? ──► ❌ 429
        │ Check (Redis) │
        └───────────────┘
                │
                ▼
        ┌───────────────┐
        │ Account       │ ──► ¿Bloqueada? ──► ❌ 403
        │ Lockout Check │
        └───────────────┘
                │
                ▼
        ┌───────────────┐
        │ Password      │ ──► ¿Incorrecta? ──► ❌ 401 + counter++
        │ Verification  │
        └───────────────┘
                │
                ▼
        ┌───────────────┐
        │ 2FA Check     │ ──► ¿Activado? ──► Solicitar código
        │ (TOTP/Backup) │
        └───────────────┘
                │
                ▼
        ┌───────────────┐
        │ Geolocation   │ ──► ¿Violación? ──► ⚠️ Alerta
        │ & Geofencing  │
        └───────────────┘
                │
                ▼
        ┌───────────────┐
        │ Device        │ ──► ¿Nuevo? ──► 📧 Email + 📱 Push
        │ Fingerprint   │
        └───────────────┘
                │
                ▼
        ┌───────────────┐
        │ HIBP Check    │ ──► ¿Breach? ──► ⚠️ Alerta
        │ (async)       │
        └───────────────┘
                │
                ▼
        ┌───────────────┐
        │ Session       │
        │ Creation (DB) │
        └───────────────┘
                │
                ▼
        ┌───────────────┐
        │ JWT + Cookie  │
        │ Response      │
        └───────────────┘
```

---

## Modelos de Seguridad

### UserSession

Cada login crea una sesión persistente en PostgreSQL:

```sql
user_sessions:
  - id: UUID
  - user_id: UUID (FK)
  - session_token: SHA-256 hash del JWT
  - device_name, device_fingerprint
  - ip_address, country
  - last_active_at, expires_at
  - is_revoked: bool
```

Ventajas:
- Revocación instantánea sin esperar JWT expiration
- Visibilidad de dispositivos conectados
- "Cerrar todas las demás sesiones"

### UserLoginLog

Registro inmutable de todos los intentos de login:

```sql
user_login_logs:
  - id, user_id, ip_address, user_agent
  - device_fingerprint, country, city
  - latitude, longitude  ← para geofencing
  - success: bool
  - created_at
```

Usado por:
- Admin Audit Panel
- Detección de nuevos dispositivos
- Geofencing (comparación con último login)

### TwoFABackupCode

```sql
two_fa_backup_codes:
  - id, user_id
  - code_hash: SHA-256 (nunca almacenamos el código en texto plano)
  - is_used, used_at
```

Generación: 8 códigos de 8 caracteres hexadecuales al activar 2FA.

### BreachCheckLog

```sql
breach_check_logs:
  - id, user_id, email
  - breaches_found: int
  - breach_names: text
  - checked_at
```

---

## Servicios de Seguridad

### geo_service.py

- `get_ip_geolocation(ip)`: Usa ip-api.com (gratuita, sin API key)
- `haversine_distance(lat1, lon1, lat2, lon2)`: Fórmula de Haversine para distancia en km
- `is_geofence_violation(...)`: Retorna (violation, distance_km)

### hibp_service.py

- `check_email_breaches(email, api_key)`: Endpoint `/breachedaccount/{email}` de HIBP v3
- `check_password_breach(password)`: PwnedPasswords API con k-anonymity (SHA-1 prefix)
- `format_breach_alert(data)`: Formatea mensaje legible

### threat_intel.py

- Detección de Tor exit nodes
- Detección de VPN ranges
- Detección de MITM headers
- Detección de User-Agents maliciosos (sqlmap, nikto, etc.)
- Risk scoring 0-100

---

## Notificaciones de Seguridad

Cascada de notificaciones cuando se detecta una amenaza:

```
Evento de Seguridad
       │
       ├──► Email al usuario (aiosmtplib)
       │
       ├──► Push notification (Web Push / pywebpush)
       │
       ├──► Webhook (Slack/Discord/Telegram)
       │
       └──► Log estructurado (JSON)
```

Eventos soportados:
- `login`, `failed_login`, `new_device`, `malware`, `brute_force`, `geofence`, `breach`, `session_revoked`

---

## Decisiones de Diseño

### ¿Por qué sesiones en DB en lugar de solo JWT?

JWT es stateless pero no permite revocación instantánea. Con sesiones en DB:
- ✅ Kill session remoto desde dashboard
- ✅ "Cerrar todas las demás sesiones"
- ✅ Detectar uso de token robado
- ⚠️ Overhead de DB query en cada request (mitigado con índice en session_token)

### ¿Por qué backup codes en vez de recovery email?

- Los backup codes funcionan **offline** (no dependen de SMTP)
- Son **criptográficamente seguros** (8 chars hex = 2^32 combinaciones)
- Se **hashean** en DB (igual que passwords)
- Son **de un solo uso** (evitan reutilización)

### ¿Por qué Haversine en vez de servicio de geocodificación pago?

- La fórmula de Haversine es **exacta** para distancias cortas/medias
- **No requiere API key** ni dependencias externas
- Suficiente para geofencing (no necesitamos dirección exacta, solo distancia)

### ¿Por qué PwnedPasswords para passwords y HIBP directo para emails?

- **Passwords**: k-anonymity garantiza que la password nunca sale del servidor. Enviamos solo 5 chars del hash SHA-1.
- **Emails**: HIBP requiere API key y no ofrece k-anonymity para emails. Pero el email ya es conocido por nuestro sistema, así que no hay fuga de privacidad adicional.
