# SellIA Setup Guide — Configuración Completa

Guía paso-a-paso para activar SellIA. Tiempo total: ~30 minutos.

---

## 1. Requisitos Previos

- [ ] Cuenta en Mercado Libre (seller)
- [ ] Cuenta en Amazon (seller, opcional)
- [ ] Cuenta en Shopify (opcional)
- [ ] Cuenta Stripe (pagos)
- [ ] WhatsApp Business Account (WABA) O WhatsApp Web en ordenador
- [ ] Google Calendar (Gmail)
- [ ] Cuentas DHL/FedEx (shipping)
- [ ] GitHub para deployments

---

## 2. Stripe Setup (Pagos)

### 2.1 Obtener API Keys

1. Ve a [stripe.com/dashboard](https://dashboard.stripe.com)
2. Inicia sesión con tu cuenta
3. Navega a **Developers** → **API Keys**
4. Copia:
   - `sk_live_xxxxx` (Secret Key — PRIVADO)
   - `pk_live_xxxxx` (Publishable Key)

### 2.2 Configurar Webhook

1. En Dashboard → **Webhooks**
2. Click **Add Endpoint**
3. URL: `https://your-domain.com/api/v1/payments/webhook`
4. Eventos: `checkout.session.completed`, `payment_intent.succeeded`, `charge.refunded`
5. Copia **Signing Secret**: `whsec_xxxxx`

### 2.3 Guardar en .env.production

```bash
STRIPE_SECRET_KEY=sk_live_xxxxx
STRIPE_PUBLISHABLE_KEY=pk_live_xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx
```

---

## 3. Mercado Libre Setup (Órdenes)

### 3.1 Obtener Credenciales OAuth

1. Ve a [Mercado Libre Developers](https://developers.mercadolibre.com.ar)
2. Crea aplicación si no tienes
3. En tu app, copia:
   - **App ID**
   - **Client Secret**
4. Autoriza a tu seller account:
   - Click **Obtener Credencial de Usuario**
   - Autoriza acceso
5. Copia:
   - **Access Token** (expires cada ~6 horas)
   - **Refresh Token** (válido 6 meses)

### 3.2 Obtener Seller ID

1. Ve a [Mis publicaciones](https://www.mercadolibre.com.ar/mis-publicaciones)
2. En URL: `https://www.mercadolibre.com.ar/publicaciones?seller_id=XXXXX`
3. Copia el número `XXXXX`

### 3.3 Guardar en .env.production

```bash
MERCADOLIBRE_SELLER_ID=123456789
MERCADOLIBRE_ACCESS_TOKEN=xxxxx
MERCADOLIBRE_REFRESH_TOKEN=xxxxx
```

---

## 4. WhatsApp Setup (Mensajes)

### Opción A: WhatsApp Business API (WABA)

1. Ve a [Facebook Business Manager](https://business.facebook.com)
2. Navega a **WhatsApp Business** → **Getting Started**
3. Crea cuenta WABA si no tienes
4. Obtén:
   - **Business Account ID**
   - **Phone Number ID**
   - **Access Token**
5. Configura webhook:
   - URL: `https://your-domain.com/api/v1/whatsapp/webhook`
   - Verify Token: cualquier string que generes

### Opción B: WhatsApp Web + Computer Use

- Sistema usa Computer Vision para controlar WhatsApp Web
- No requiere API keys
- Recomendado para comenzar (gratis)

### 4.1 Guardar en .env.production

```bash
WHATSAPP_MODE=api  # o "computer_use"
WHATSAPP_BUSINESS_ACCOUNT_ID=123456789
WHATSAPP_PHONE_NUMBER_ID=987654321
WHATSAPP_API_TOKEN=xxxxx
WHATSAPP_VERIFY_TOKEN=verify_me_12345
```

---

## 5. Google Calendar Setup (Scheduling)

### 5.1 Crear Proyecto Google Cloud

1. Ve a [Google Cloud Console](https://console.cloud.google.com)
2. Crea proyecto nuevo: **SellIA**
3. Habilita **Google Calendar API**

### 5.2 Obtener API Key

1. Ve a **Credentials**
2. Click **Create Credentials** → **API Key**
3. Copia la key
4. Restrict a **Calendar API**

### 5.3 Obtener Calendar ID

1. Ve a [Google Calendar](https://calendar.google.com)
2. Settings → tu calendario
3. Copia **Calendar ID** (email-like)

### 5.4 Guardar en .env.production

```bash
GOOGLE_CALENDAR_API_KEY=AIzaSy...
GOOGLE_CALENDAR_ID=your-email@gmail.com
```

---

## 6. Shipping Setup (DHL/FedEx)

### 6.1 DHL Setup

1. Ve a [DHL Developer Portal](https://developer.dhl.com)
2. Sign up / Login
3. Obtén:
   - **API Key**
   - **Account Number**

### 6.2 FedEx Setup

1. Ve a [FedEx Developer Resources](https://developer.fedex.com)
2. Crea cuenta developer
3. Obtén:
   - **API Key**
   - **Secret Key**
   - **Account Number**

### 6.3 Guardar en .env.production

```bash
DHL_API_KEY=xxxxx
DHL_ACCOUNT_NUMBER=12345678
FEDEX_API_KEY=xxxxx
FEDEX_SECRET_KEY=xxxxx
FEDEX_ACCOUNT_NUMBER=999999999
```

---

## 7. Amazon Setup (Opcional)

### 7.1 MWS Credentials

1. Ve a [Amazon Seller Central](https://sellercentral.amazon.com)
2. Settings → **User Permissions** → **MWS Authorization**
3. Obtén:
   - **MWS Key**
   - **MWS Secret**
   - **Seller ID**

### 7.2 Guardar en .env.production

```bash
AMAZON_MWS_KEY=xxxxx
AMAZON_MWS_SECRET=xxxxx
AMAZON_SELLER_ID=A1234567890ABC
```

---

## 8. Shopify Setup (Opcional)

### 8.1 Crear App Private

1. Ve a Shopify Admin → **Settings** → **Apps & Integrations** → **Develop Apps**
2. Crea nuevo app
3. En Admin API scopes, activa:
   - `read_orders`
   - `read_fulfillments`
   - `write_fulfillments`
4. Obtén:
   - **API Key**
   - **API Secret**

### 8.2 Guardar en .env.production

```bash
SHOPIFY_STORE_URL=your-store.myshopify.com
SHOPIFY_API_KEY=xxxxx
SHOPIFY_API_PASSWORD=xxxxx
```

---

## 9. Database Setup

### 9.1 PostgreSQL

```bash
# Local o RDS AWS

DATABASE_URL=postgresql://user:password@localhost:5432/sellias_db

# Ejecutar migrations
alembic upgrade head
```

### 9.2 Redis (Caching)

```bash
REDIS_URL=redis://localhost:6379/0
```

---

## 10. Deploy a Producción

### 10.1 Vercel

```bash
cd frontend
vercel --prod
```

### 10.2 Backend (Railway/Fly.io/AWS)

```bash
# Copiar .env.production a servidor
# Deploy: git push heroku main (si Heroku) o similar
```

---

## 11. Verificación Rápida

### 11.1 Test Stripe

```bash
curl -X POST https://your-domain.com/api/v1/payments/checkout \
  -d '{"product": {"id": "test", "name": "Test", "price": 10}, "buyer": {"email": "test@test.com"}}' \
  -H "Content-Type: application/json"
```

Esperado: `checkout_url` + `session_id`

### 11.2 Test Mercado Libre

```bash
curl https://your-domain.com/api/v1/orders/sync?seller_id=YOUR_ID \
  -H "Authorization: Bearer YOUR_ML_TOKEN"
```

Esperado: `orders_synced: 0+`

### 11.3 Test WhatsApp

```bash
curl -X POST https://your-domain.com/api/v1/whatsapp/webhook \
  -d '{"entry": [{"messaging": [{"sender": {"id": "123"}, "message": {"text": "Hola"}}]}]}' \
  -H "Content-Type: application/json"
```

Esperado: `status: success`

---

## 12. Monitoreo

### 12.1 Logs

```bash
# Vercel
vercel logs

# Backend
tail -f /var/log/sellias.log
```

### 12.2 Dashboard Stripe

Ve a [Stripe Dashboard](https://dashboard.stripe.com) → **Payments** para ver transacciones

### 12.3 Dashboard SellIA

Accede a `https://your-domain.com/dashboard` para ver KPIs real-time

---

## 13. Troubleshooting

| Problema | Solución |
|----------|----------|
| Webhook Stripe no funciona | Verifica webhook secret en .env. Revisa IP whitelist. |
| ML token expirado | Refresh token automático. Si falla: re-autoriza en [Developers](https://developers.mercadolibre.com.ar) |
| Órdenes no syncan | Check seller_id correcto. ML API key válida. Firewall abierto. |
| WhatsApp no responde | Verifica WABA token activo. Número de teléfono verificado. |
| Shipping labels fallan | API key DHL/FedEx válida. Dirección destino completa. |

---

## 14. Checklist Finalización

- [ ] Stripe keys en .env
- [ ] ML seller_id + tokens
- [ ] WhatsApp configurado (API o Web)
- [ ] Google Calendar API key
- [ ] DHL/FedEx keys
- [ ] Database migraciones OK
- [ ] Redis running
- [ ] Frontend deployed
- [ ] Backend deployed
- [ ] Webhooks verificados
- [ ] Logs sin errores
- [ ] Test transacción OK

**¡LISTO! SellIA activo. Sistema operativo 24/7.**

---

## 15. Support

Email: support@sellias.com
Docs: https://docs.sellias.com
API Reference: https://api.sellias.com/docs
