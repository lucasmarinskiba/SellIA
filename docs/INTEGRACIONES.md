# Integraciones externas

Qué API le falta a cada herramienta para funcionar completa, cuánto cuesta y qué
variable de entorno hay que cargar en Railway (Variables → New Variable) o en el
gestor de secretos que se use.

**Generado desde `backend/app/domains/integrations/registry.py`** — no editar a
mano: correr `python backend/scripts/gen_integrations_doc.py`.

El estado real de esta instalación (qué está cargado y qué falta) se consulta en
vivo con `GET /api/v1/integrations/status`, que lee el entorno de verdad. Este
documento describe el catálogo; ese endpoint describe el deploy.

## Regla que sigue el producto

Sin la API, ninguna pantalla inventa el número: dice que no puede medirlo. Estas
claves reemplazan ese mensaje por datos reales, no arreglan un dato falso.


## Resumen por prioridad

| Prioridad | Integración | Herramienta | Costo | Variables |
| --- | --- | --- | --- | --- |
| 🔴 Primero | Anthropic (Claude) | Agentes IA | pago | `ANTHROPIC_API_KEY` |
| 🔴 Primero | Resend | Notificaciones | free tier + pago | `RESEND_API_KEY` |
| 🔴 Primero | MercadoPago | Pagos | pago | `MERCADOPAGO_ACCESS_TOKEN` |
| 🔴 Primero | Google Search Console API | SEO | gratis | `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET` |
| 🔴 Primero | PageSpeed Insights API | SEO | gratis | `GOOGLE_PAGESPEED_API_KEY` |
| 🔴 Primero | App de Meta (WhatsApp / Instagram / Messenger) | Vendedor Multiplataforma | gratis | `META_APP_ID`, `META_APP_SECRET` |
| 🔴 Primero | Aplicación de MercadoLibre | Vendedor Multiplataforma | gratis | `MERCADO_LIBRE_CLIENT_ID`, `MERCADO_LIBRE_CLIENT_SECRET` |
| 🟡 Después | Google Analytics 4 Data API | Analytics | gratis | `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET`, `GA4_PROPERTY_ID` |
| 🟡 Después | Google Business Profile API | Construya Autoridad | gratis | `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET` |
| 🟡 Después | Sentry | Operación | free tier + pago | `SENTRY_DSN` |
| 🟡 Después | Volumen y dificultad de keywords | SEO | pago | `KEYWORD_API_PROVIDER`, `KEYWORD_API_KEY` |
| ⚪ Cuando haga falta | OpenAI | Agentes IA | pago | `OPENAI_API_KEY` |
| ⚪ Cuando haga falta | Meta Marketing API (insights) | Analytics | gratis | `META_APP_ID`, `META_APP_SECRET` |
| ⚪ Cuando haga falta | Twilio | Notificaciones | pago | `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER` |
| ⚪ Cuando haga falta | Stripe | Pagos | pago | `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET` |
| ⚪ Cuando haga falta | Bing Webmaster Tools API | SEO | gratis | `BING_WEBMASTER_API_KEY` |
| ⚪ Cuando haga falta | Índice de backlinks | SEO / Construya Autoridad | pago | `BACKLINK_API_PROVIDER`, `BACKLINK_API_KEY` |
| ⚪ Cuando haga falta | Amazon Selling Partner API | Vendedor Multiplataforma | gratis | `AMAZON_CLIENT_ID`, `AMAZON_CLIENT_SECRET` |
| ⚪ Cuando haga falta | Aplicación de Hotmart | Vendedor Multiplataforma | gratis | `HOTMART_CLIENT_ID`, `HOTMART_CLIENT_SECRET` |

## SEO

### Google Search Console API

- **Proveedor:** Google
- **Costo:** gratis
- **Prioridad:** 🔴 Primero
- **Variables requeridas:** `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET`
- **Cómo obtenerla:** https://developers.google.com/webmaster-tools/v1/getting_started
- **Qué desbloquea:** Posiciones, impresiones, clics y CTR reales por keyword y por página, sacados de las búsquedas que de verdad mostraron el sitio del usuario. Es la única fuente de posiciones reales y no cuesta nada.
- **Qué hace hoy sin esto:** La herramienta mide la página pero no puede decir en qué puesto sale ni por qué términos la encuentran.

### PageSpeed Insights API

- **Proveedor:** Google
- **Costo:** gratis
- **Prioridad:** 🔴 Primero
- **Variables requeridas:** `GOOGLE_PAGESPEED_API_KEY`
- **Cómo obtenerla:** https://developers.google.com/speed/docs/insights/v5/get-started
- **Qué desbloquea:** Core Web Vitals reales (LCP, CLS, INP) de laboratorio y de campo (CrUX), que hoy se declaran explícitamente como no medibles.
- **Qué hace hoy sin esto:** Sólo se mide el tiempo de respuesta del servidor, que es real pero es una parte chica de la experiencia.

### Volumen y dificultad de keywords

- **Proveedor:** DataForSEO (barato) · SemRush · Ahrefs · Moz
- **Costo:** pago
- **Prioridad:** 🟡 Después
- **Variables requeridas:** `KEYWORD_API_PROVIDER`, `KEYWORD_API_KEY`
- **Opcionales:** `KEYWORD_API_LOGIN`
- **Cómo obtenerla:** https://docs.dataforseo.com/v3/keywords_data/overview/
- **Qué desbloquea:** Cuánta gente busca cada término y qué tan difícil es rankear. Convierte el perfil de términos actual (qué dice tu página) en decisiones de qué escribir.
- **Qué hace hoy sin esto:** Se muestra qué términos usa realmente la página, sin volumen ni dificultad, y se aclara que eso requiere API paga.

### Bing Webmaster Tools API

- **Proveedor:** Microsoft
- **Costo:** gratis
- **Prioridad:** ⚪ Cuando haga falta
- **Variables requeridas:** `BING_WEBMASTER_API_KEY`
- **Cómo obtenerla:** https://learn.microsoft.com/en-us/bingwebmaster/getting-access
- **Qué desbloquea:** Posiciones en Bing y envío instantáneo de URLs a indexar (IndexNow). Gratis y con menos competencia que Google.
- **Qué hace hoy sin esto:** No se consulta Bing.

## SEO / Construya Autoridad

### Índice de backlinks

- **Proveedor:** Ahrefs · Majestic · Moz · DataForSEO
- **Costo:** pago
- **Prioridad:** ⚪ Cuando haga falta
- **Variables requeridas:** `BACKLINK_API_PROVIDER`, `BACKLINK_API_KEY`
- **Cómo obtenerla:** https://docs.dataforseo.com/v3/backlinks/overview/
- **Qué desbloquea:** Quién enlaza al sitio del usuario desde afuera: el otro 50% de la autoridad. Hoy sólo se verifica el enlazado entre las propiedades del propio usuario.
- **Qué hace hoy sin esto:** Se mide la red interna de marca (web ↔ redes ↔ tienda), que es real y accionable, pero no ve enlaces de terceros.

## Analytics

### Google Analytics 4 Data API

- **Proveedor:** Google
- **Costo:** gratis
- **Prioridad:** 🟡 Después
- **Variables requeridas:** `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET`, `GA4_PROPERTY_ID`
- **Cómo obtenerla:** https://developers.google.com/analytics/devguides/reporting/data/v1
- **Qué desbloquea:** Visitas, origen del tráfico y conversiones del sitio del usuario, para cruzar tráfico con las conversaciones que sí medimos hoy.
- **Qué hace hoy sin esto:** Analytics sólo lee conversaciones, mensajes y órdenes propias: no sabe cuánta gente visitó la web sin escribir.

### Meta Marketing API (insights)

- **Proveedor:** Meta
- **Costo:** gratis
- **Prioridad:** ⚪ Cuando haga falta
- **Variables requeridas:** `META_APP_ID`, `META_APP_SECRET`
- **Opcionales:** `META_AD_ACCOUNT_ID`
- **Cómo obtenerla:** https://developers.facebook.com/docs/marketing-api/insights
- **Qué desbloquea:** Inversión publicitaria y resultados reales para poder calcular ROAS. Sin gasto real, cualquier ROI sería inventado.
- **Qué hace hoy sin esto:** No se muestra ROI ni ROAS en ninguna pantalla, justamente por eso.

## Vendedor Multiplataforma

### App de Meta (WhatsApp / Instagram / Messenger)

- **Proveedor:** Meta
- **Costo:** gratis
- **Prioridad:** 🔴 Primero
- **Variables requeridas:** `META_APP_ID`, `META_APP_SECRET`
- **Opcionales:** `META_WEBHOOK_VERIFY_TOKEN`
- **Cómo obtenerla:** https://developers.facebook.com/docs/whatsapp/cloud-api/get-started
- **Qué desbloquea:** Botón 'Autorizar' con OAuth: hoy cada usuario tiene que pegar a mano un token que sacó por su cuenta del panel de Meta.
- **Qué hace hoy sin esto:** El usuario carga sus credenciales manualmente en el formulario y se validan de verdad contra la plataforma.

### Aplicación de MercadoLibre

- **Proveedor:** MercadoLibre
- **Costo:** gratis
- **Prioridad:** 🔴 Primero
- **Variables requeridas:** `MERCADO_LIBRE_CLIENT_ID`, `MERCADO_LIBRE_CLIENT_SECRET`
- **Opcionales:** `MERCADO_LIBRE_REDIRECT_URI`
- **Cómo obtenerla:** https://developers.mercadolibre.com.ar/es_ar/registra-tu-aplicacion
- **Qué desbloquea:** Conexión con un clic y renovación automática del token, para que la IA responda preguntas de publicaciones sin que se corte cada 6 horas.
- **Qué hace hoy sin esto:** Cada usuario tiene que crear su propia app en ML y pegar client_id y client_secret.

### Amazon Selling Partner API

- **Proveedor:** Amazon
- **Costo:** gratis
- **Prioridad:** ⚪ Cuando haga falta
- **Variables requeridas:** `AMAZON_CLIENT_ID`, `AMAZON_CLIENT_SECRET`
- **Cómo obtenerla:** https://developer-docs.amazon.com/sp-api/docs/registering-your-application
- **Qué desbloquea:** Órdenes, listings y mensajes de Amazon en el mismo inbox. Requiere aprobación de Amazon, que tarda.
- **Qué hace hoy sin esto:** El usuario carga sus propias credenciales SP-API si ya tiene una app aprobada.

### Aplicación de Hotmart

- **Proveedor:** Hotmart
- **Costo:** gratis
- **Prioridad:** ⚪ Cuando haga falta
- **Variables requeridas:** `HOTMART_CLIENT_ID`, `HOTMART_CLIENT_SECRET`
- **Opcionales:** `HOTMART_REDIRECT_URI`
- **Cómo obtenerla:** https://developers.hotmart.com/docs/en/start/app-auth/
- **Qué desbloquea:** Ventas y suscripciones de infoproductos sincronizadas.
- **Qué hace hoy sin esto:** Credenciales manuales por usuario.

## Construya Autoridad

### Google Business Profile API

- **Proveedor:** Google
- **Costo:** gratis
- **Prioridad:** 🟡 Después
- **Variables requeridas:** `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET`
- **Cómo obtenerla:** https://developers.google.com/my-business/content/prereqs
- **Qué desbloquea:** Reseñas reales de Google, respuesta automática a reseñas y ficha local: la señal de autoridad más fuerte para un negocio con local físico.
- **Qué hace hoy sin esto:** Sólo se cuentan reseñas cargadas manualmente en SellIA.

## Agentes IA

### Anthropic (Claude)

- **Proveedor:** Anthropic
- **Costo:** pago
- **Prioridad:** 🔴 Primero
- **Variables requeridas:** `ANTHROPIC_API_KEY`
- **Cómo obtenerla:** https://docs.anthropic.com/en/api/getting-started
- **Qué desbloquea:** Respuestas generadas por el agente en conversaciones y análisis.
- **Qué hace hoy sin esto:** Sin clave, el sistema cae a respuestas de plantilla.

### OpenAI

- **Proveedor:** OpenAI
- **Costo:** pago
- **Prioridad:** ⚪ Cuando haga falta
- **Variables requeridas:** `OPENAI_API_KEY`
- **Cómo obtenerla:** https://platform.openai.com/docs/quickstart
- **Qué desbloquea:** Proveedor alternativo y embeddings para búsqueda semántica del catálogo.
- **Qué hace hoy sin esto:** Se usa sólo Anthropic; si falla, no hay segundo proveedor.

## Notificaciones

### Resend

- **Proveedor:** Resend
- **Costo:** free tier + pago
- **Prioridad:** 🔴 Primero
- **Variables requeridas:** `RESEND_API_KEY`
- **Opcionales:** `RESEND_WEBHOOK_SECRET`
- **Cómo obtenerla:** https://resend.com/docs/introduction
- **Qué desbloquea:** Envío de emails transaccionales y seguimiento de aperturas.
- **Qué hace hoy sin esto:** Ya está configurado y en uso.

### Twilio

- **Proveedor:** Twilio
- **Costo:** pago
- **Prioridad:** ⚪ Cuando haga falta
- **Variables requeridas:** `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`
- **Cómo obtenerla:** https://www.twilio.com/docs/messaging/quickstart
- **Qué desbloquea:** SMS de aviso al vendedor cuando entra una consulta caliente fuera de la app.
- **Qué hace hoy sin esto:** Las notificaciones viven dentro de la app y por email.

## Operación

### Sentry

- **Proveedor:** Sentry
- **Costo:** free tier + pago
- **Prioridad:** 🟡 Después
- **Variables requeridas:** `SENTRY_DSN`
- **Cómo obtenerla:** https://docs.sentry.io/platforms/python/integrations/fastapi/
- **Qué desbloquea:** Errores de producción con stack trace en vez de tener que leer logs de Railway a mano. Free tier alcanza de sobra para este volumen.
- **Qué hace hoy sin esto:** Los errores se ven sólo en los logs del deploy.

## Pagos

### MercadoPago

- **Proveedor:** MercadoPago
- **Costo:** pago
- **Prioridad:** 🔴 Primero
- **Variables requeridas:** `MERCADOPAGO_ACCESS_TOKEN`
- **Opcionales:** `MERCADOPAGO_PUBLIC_KEY`, `MERCADOPAGO_WEBHOOK_SECRET`
- **Cómo obtenerla:** https://www.mercadopago.com.ar/developers/es/docs
- **Qué desbloquea:** Checkout y cobros en Argentina y Latam.
- **Qué hace hoy sin esto:** Ya está configurado y en uso.

### Stripe

- **Proveedor:** Stripe
- **Costo:** pago
- **Prioridad:** ⚪ Cuando haga falta
- **Variables requeridas:** `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`
- **Opcionales:** `STRIPE_PUBLISHABLE_KEY`
- **Cómo obtenerla:** https://docs.stripe.com/keys
- **Qué desbloquea:** Cobro internacional con tarjeta, además de MercadoPago que ya está andando.
- **Qué hace hoy sin esto:** Sólo MercadoPago (configurado).

## Cómo cargarlas en Railway

```bash
# Una por una, desde la raíz del repo (railway link ya hecho):
railway variables --set "GOOGLE_PAGESPEED_API_KEY=tu-clave"

# Verificar qué quedó cargado (nombres, no valores):
railway variables
```

Railway reinicia el servicio al cambiar una variable. Después de cargarlas, `GET /api/v1/integrations/status` debería mostrarlas como `configured: true`.
