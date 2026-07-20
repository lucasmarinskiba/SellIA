# Cloudflare Turnstile - Guía de Configuración

Cloudflare Turnstile es un CAPTCHA invisible que protege los formularios de login y registro contra bots automatizados, sin degradar la experiencia del usuario.

## ¿Qué es Turnstile?

A diferencia de reCAPTCHA, Turnstile:
- **No requiere puzzles** (seleccionar imágenes, etc.)
- **No rastrea usuarios** para publicidad
- Funciona de forma **completamente invisible** en la mayoría de los casos
- Es **gratuito** sin límites de solicitudes

---

## Paso 1: Obtener las claves de Cloudflare

1. Ir a [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. Navegar a **Turnstile** en el menú lateral
3. Click en **Add Widget**
4. Completar:
   - **Widget Name**: `SellIA Login Protection`
   - **Hostname**: tu dominio (ej: `tusitio.com`)
   - Para desarrollo local, agregar también `localhost`
5. Click en **Create**

Cloudflare te dará dos claves:

| Clave | Uso | Ejemplo |
|-------|-----|---------|
| **Site Key** | Frontend (pública) | `0x4AAAAAA...` |
| **Secret Key** | Backend (privada) | `0x4AAAAAA...` |

---

## Paso 2: Configurar el Backend

Agregar la secret key a las variables de entorno:

```bash
# .env o docker-compose.yml
TURNSTILE_SECRET_KEY=0x4AAAAAAxxxxxxxxxxxxxxxxxxxxxx
```

Reiniciar el contenedor:

```bash
docker compose restart backend
```

### Comportamiento por entorno

El backend tiene fallback inteligente:

| Entorno | TURNSTILE_SECRET_KEY | Comportamiento |
|---------|----------------------|----------------|
| `development` | Vacío | ✅ Turnstile se omite automáticamente |
| `development` | Configurado | ✅ Se valida normalmente |
| `production` | Vacío | ❌ Login/register rechazados con error 400 |
| `production` | Configurado | ✅ Se valida estrictamente |

---

## Paso 3: Configurar el Frontend

Agregar la site key al frontend:

```bash
# frontend/.env.local
NEXT_PUBLIC_TURNSTILE_SITE_KEY=0x4AAAAAAxxxxxxxxxxxxxxxxxxxxxx
```

Reiniciar el frontend:

```bash
docker compose restart frontend
```

### Cómo funciona en el Login

El frontend carga el script de Turnstile automáticamente:

```html
<script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer></script>
```

Cuando el usuario hace submit del formulario:

1. Turnstile genera un token único en el navegador
2. El frontend envía el token en el header: `X-Turnstile-Token: <token>`
3. El backend verifica el token contra `challenges.cloudflare.com`
4. Si es válido, continúa con el login normal

### Código de ejemplo (React)

```tsx
// En tu formulario de login
useEffect(() => {
  if (document.getElementById('turnstile-script')) return
  const script = document.createElement('script')
  script.id = 'turnstile-script'
  script.src = 'https://challenges.cloudflare.com/turnstile/v0/api.js'
  script.async = true
  script.defer = true
  document.body.appendChild(script)

  window.turnstileCallback = (token: string) => {
    setTurnstileToken(token)
  }
}, [])

// En el submit
const handleSubmit = async (e) => {
  e.preventDefault()
  const data = await auth.login({
    email,
    password,
    turnstileToken: turnstileToken || undefined,
  })
}
```

---

## Paso 4: Verificar que funciona

### Test en desarrollo (sin clave)

```bash
curl -X POST http://localhost/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=password123"
```

✅ Debe funcionar sin `X-Turnstile-Token`

### Test en desarrollo (con clave)

```bash
curl -X POST http://localhost/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "X-Turnstile-Token: dummy-token-for-testing" \
  -d "username=test@example.com&password=password123"
```

⚠️ Con clave configurada, Turnstile valida el token. Usar un token real del navegador para testear.

---

## Troubleshooting

### "Verificación de seguridad fallida"

Significa que el token de Turnstile fue rechazado por Cloudflare.

**Causas comunes:**
- Token expirado (válido solo 5 minutos)
- Dominio no autorizado en la configuración de Cloudflare
- Token reutilizado (solo se puede verificar una vez)

**Solución:**
1. Verificar que el dominio esté en la lista de hostnames de Turnstile
2. Para desarrollo local, agregar `localhost` a los hostnames
3. Recargar la página para obtener un token nuevo

### Login funciona sin token en producción

Significa que `TURNSTILE_SECRET_KEY` no está configurada. Revisar:

```bash
docker compose exec backend env | grep TURNSTILE
```

Si está vacío, agregarla al `.env` y reiniciar.

### "Widget not found" en frontend

El script de Turnstile no cargó. Verificar:
1. Que `NEXT_PUBLIC_TURNSTILE_SITE_KEY` esté definida
2. Que no haya adblockers bloqueando `challenges.cloudflare.com`
3. Que el elemento HTML tenga la clase `cf-turnstile`

---

## Configuración Avanzada

### Forzar Turnstile en desarrollo

Para testear Turnstile localmente con clave real:

```bash
# .env
ENVIRONMENT=development
TURNSTILE_SECRET_KEY=tu-clave-real
```

### Múltiples widgets

Si tenés varios formularios (login, register, recuperar password), cada uno necesita su propio widget con `data-callback` diferente.

### Tema oscuro

```html
<div class="cf-turnstile"
     data-sitekey="TU_SITE_KEY"
     data-theme="dark"
     data-callback="turnstileCallback">
</div>
```

Opciones de `data-theme`: `light`, `dark`, `auto`

---

## Referencias

- [Documentación oficial Turnstile](https://developers.cloudflare.com/turnstile/)
- [Client-side rendering](https://developers.cloudflare.com/turnstile/get-started/client-side-rendering/)
- [Server-side validation](https://developers.cloudflare.com/turnstile/get-started/server-side-validation/)
