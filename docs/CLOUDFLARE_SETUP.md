# 🌐 SellIA + Cloudflare — Guía de Configuración Paso a Paso

## 1. Requisitos Previos

- Dominio propio apuntando a Cloudflare (ej. `app.sellia.com`)
- Acceso al panel de Cloudflare

## 2. DNS Configuration

1. Ir a **DNS → Records**
2. Crear un registro `A`:
   - Name: `app` (o `@` para root)
   - IPv4: `<IP_DE_TU_SERVIDOR>`
   - Proxy status: 🟡 Proxied (esto activa Cloudflare)
3. Crear un registro `CNAME` para `www` si es necesario.

## 3. SSL/TLS Settings

Ir a **SSL/TLS → Overview** y seleccionar:
- **Encryption mode:** `Full (strict)`
  - Esto fuerza HTTPS entre Cloudflare ↔ tu servidor
  - Requiere un certificado válido en tu servidor (Let's Encrypt o Cloudflare Origin CA)

### 3.1 Origin Server Certificate (recomendado)
1. Ir a **SSL/TLS → Origin Server**
2. Click **Create Certificate**
3. Seleccionar:
   - Private key type: RSA (2048)
   - Hostnames: `app.sellia.com`, `*.app.sellia.com`
   - Certificate Validity: 15 years
4. Copiar el **Origin Certificate** a `./certs/fullchain.pem`
5. Copiar la **Private Key** a `./certs/privkey.pem`
6. Estos archivos ya están mapeados en `docker-compose.prod.yml`

## 4. Always Use HTTPS

Ir a **SSL/TLS → Edge Certificates**:
- Activar **Always Use HTTPS**: ON

## 5. Security Headers (Opcional)

Cloudflare puede inyectar headers adicionales:
1. Ir a **Rules → Transform Rules → Modify Response Header**
2. Crear regla:
   - When: `Custom filter expression` → `(http.host eq "app.sellia.com")`
   - Then:
     - Set static: `Strict-Transport-Security` = `max-age=63072000; includeSubDomains; preload`

## 6. Page Rules (Crítico para API)

Ir a **Rules → Page Rules** y crear:

### Rule 1: No cachear API
- URL: `app.sellia.com/api/*`
- Settings:
  - Cache Level: Bypass
  - Security Level: High
  - Browser Integrity Check: On

### Rule 2: Proteger autenticación
- URL: `app.sellia.com/api/v1/auth/*`
- Settings:
  - Security Level: I'm Under Attack
  - Browser Integrity Check: On

## 7. Bot Fight Mode

Ir a **Security → Bots**:
- Activar **Bot Fight Mode**: ON
- O suscribirse a **Super Bot Fight Mode** para controles más granulares

## 8. Firewall Rules

Ir a **Security → WAF → Custom rules**:

### Rule 1: Bloquear países de alto riesgo
- Expression: `(ip.geoip.country in {"CN" "RU" "KP" "IR"})`
- Action: Block

### Rule 2: Rate limiting en login
- Expression: `(http.request.uri.path contains "/api/v1/auth/login")`
- Action: Block (o Challenge)
- Rate limit: 5 requests per minute

## 9. Authenticated Origin Pulls (mTLS)

Ir a **SSL/TLS → Origin Server**:
1. Activar **Authenticated Origin Pulls**: ON
2. Esto hace que Nginx solo acepte conexiones de Cloudflare

## 10. Verificación

```bash
# Verificar que Cloudflare está protegiendo
curl -I https://app.sellia.com/api/v1/auth/security-status
# Debería ver: cf-ray, cf-cache-status, etc.

# Verificar que no cachea API
curl -I https://app.sellia.com/api/v1/users
# Debería ver: cf-cache-status: DYNAMIC (o BYPASS)
```

## 11. Cloudflare Turnstile (CAPTCHA invisible)

Ir a **Turnstile** en el panel de Cloudflare:
1. Crear un nuevo widget
2. Dominios: `app.sellia.com`, `localhost` (para dev)
3. Copiar **Site Key** → `NEXT_PUBLIC_TURNSTILE_SITE_KEY`
4. Copiar **Secret Key** → `TURNSTILE_SECRET_KEY`
