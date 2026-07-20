# Platforms Integration Implementation Guide

Complete guide for integrating 6 new platforms into SellIA + FeedIA ecosystem.

## Overview

Implementing 6 e-commerce & communication platforms:

1. **Facebook Shop** (5 hours) — Orders, inventory, tracking
2. **Instagram Shop** (4 hours) — Direct checkout, Reels integration
3. **TikTok Shop** (5 hours) — Real-time orders, fulfillment
4. **Calendly** (3 hours) — Event sync, reminders, Google Calendar
5. **Slack** (4 hours) — Bot commands, alerts, analytics
6. **Telegram** (4 hours) — Bot, push notifications, deep links

**Total: 25 hours of implementation**

---

## Architecture Overview

### Database Layer
**File:** `backend/app/core/database/platform_models.py`

All platform models use PostgreSQL via SQLAlchemy ORM:

- **Platform-Specific Tables:**
  - `facebook_shops`, `facebook_products`, `facebook_orders`
  - `instagram_shops`, `instagram_products`, `instagram_orders`
  - `tiktok_shops`, `tiktok_products`, `tiktok_orders`
  - `calendly_accounts`, `calendly_events`
  - `slack_workspaces`, `slack_commands`, `slack_messages`
  - `telegram_bots`, `telegram_users`, `telegram_messages`

- **Shared Tables:**
  - `platform_webhook_events` — Unified webhook log for all platforms
  - `platform_credentials` — Encrypted credential storage
  - `platform_rate_limits` — Rate limit tracking per platform
  - `platform_sync_status` — Sync status for each platform

### Integration Layer

**Directory:** `backend/app/core/integrations/`

Each platform has a dedicated automation class with full implementation:

```
facebook_shop_automation.py      → FacebookShopAutomation
instagram_shop_automation.py     → InstagramShopAutomation
tiktok_shop_automation.py        → TikTokShopAutomation
calendly_automation.py           → CalendlyAutomation
slack_automation.py              → SlackAutomation
telegram_automation.py           → TelegramAutomation
```

### API Layer

**File:** `backend/app/api/v1/platforms_integration.py`

Unified FastAPI router with endpoints for all platforms:

```
POST   /api/v1/platforms/{platform}/webhooks/events
POST   /api/v1/platforms/{platform}/config
POST   /api/v1/platforms/{platform}/sync/{resource}
GET    /api/v1/platforms/{platform}/{resource}
GET    /api/v1/platforms/health
GET    /api/v1/platforms/status
```

---

## Implementation Steps

### Phase 1: Database & Models (1 hour)

1. **Create platform models:**
   ```bash
   cd backend
   # Models already created in platform_models.py
   ```

2. **Run migrations:**
   ```bash
   alembic revision --autogenerate -m "Add platform models"
   alembic upgrade head
   ```

3. **Verify tables created:**
   ```sql
   SELECT tablename FROM pg_tables WHERE tablename LIKE 'facebook_%' OR tablename LIKE 'instagram_%' ...
   ```

### Phase 2: Facebook Shop (5 hours)

#### 2.1 Setup (30 minutes)
- Register app on Facebook Developers Console
- Get App ID, App Secret, Webhook Verify Token
- Create shop catalog

#### 2.2 Implement Automation (2.5 hours)
```python
from app.core.integrations.facebook_shop_automation import FacebookShopAutomation

# Initialize
fb_shop = FacebookShopAutomation(
    shop_id="123456",
    access_token="eaa...",
    webhook_verify_token="verify_token",
    catalog_id="catalog_123"
)

# Webhook handling
await fb_shop.handle_webhook(payload)

# Order confirmation
await fb_shop.confirm_order(order_id)

# Product sync
products = await fb_shop.sync_products_from_facebook()
await fb_shop.sync_products_to_facebook(products)

# Inventory management
await fb_shop.update_inventory(product_id, quantity=50)

# Tracking updates
await fb_shop.update_tracking(order_id, "FedEx", "1Z999AA...")
```

#### 2.3 API Endpoints (1 hour)
```python
POST   /api/v1/platforms/facebook-shop/webhooks/orders
POST   /api/v1/platforms/facebook-shop/config
POST   /api/v1/platforms/facebook-shop/sync/products
GET    /api/v1/platforms/facebook-shop/orders/{order_id}
```

#### 2.4 Testing (1 hour)
- Test webhook signature verification
- Mock order events
- Verify DB persistence
- Test inventory sync

### Phase 3: Instagram Shop (4 hours)

#### 3.1 Implementation (2 hours)
```python
from app.core.integrations.instagram_shop_automation import InstagramShopAutomation

ig_shop = InstagramShopAutomation(
    account_id="ig_account_123",
    access_token="eaa...",
    webhook_verify_token="verify_token"
)

# Handle checkout orders
await ig_shop.handle_webhook(payload)

# Product sync
await ig_shop.sync_products_to_instagram(products)

# Direct checkout
checkout_url = await ig_shop.create_checkout_link(product_id)

# Analytics
analytics = await ig_shop.get_shop_analytics()

# Tracking
await ig_shop.update_tracking(order_id, "DHL", "tracking_num")

# DM integration
await ig_shop.send_order_confirmation_dm(order_id, user_id, message)
```

#### 3.2 Endpoints (1 hour)
```python
POST   /api/v1/platforms/instagram-shop/webhooks/orders
POST   /api/v1/platforms/instagram-shop/sync/products
GET    /api/v1/platforms/instagram-shop/analytics
```

#### 3.3 Testing (1 hour)
- Payment flow simulation
- Analytics validation

### Phase 4: TikTok Shop (5 hours)

#### 4.1 OAuth & Setup (1.5 hours)
- Register seller app on TikTok Developer Console
- OAuth flow implementation
- Token refresh mechanism

#### 4.2 Core Automation (2.5 hours)
```python
from app.core.integrations.tiktok_shop_automation import TikTokShopAutomation

tt_shop = TikTokShopAutomation(
    shop_id="123456",
    shop_cipher="encrypted_shop_id",
    access_token="token...",
    refresh_token="refresh_token...",
    webhook_verify_token="verify_token"
)

# Webhook handling
await tt_shop.handle_webhook(payload)

# Order management
order = await tt_shop.get_order_details(order_id)
await tt_shop.confirm_order(order_id)
orders = await tt_shop.list_orders(page=1, status_filter=["100", "110"])

# Product catalog
await tt_shop.sync_products_to_tiktok(products)
await tt_shop.update_inventory(product_id, quantity=100)

# Fulfillment
await tt_shop.create_shipment(order_id, fulfillment_type, tracking_info)

# Rate limits
quota = await tt_shop.check_rate_limit()
```

#### 4.3 Endpoints (1 hour)
```python
POST   /api/v1/platforms/tiktok-shop/webhooks/orders
POST   /api/v1/platforms/tiktok-shop/config
POST   /api/v1/platforms/tiktok-shop/sync/orders
```

### Phase 5: Calendly (3 hours)

#### 5.1 Implementation (1.5 hours)
```python
from app.core.integrations.calendly_automation import CalendlyAutomation

calendly = CalendlyAutomation(
    access_token="token...",
    webhook_uuid="existing_webhook_uuid"
)

# Webhook setup
webhook_uuid = await calendly.register_webhook(webhook_url, user_uri)

# Event handling
await calendly.handle_webhook(payload)

# Event management
events = await calendly.list_events(user_uri, status="scheduled")
details = await calendly.get_event_details(event_uuid)
await calendly.cancel_event(event_uuid, reason="Rescheduled")

# Google Calendar sync
await calendly.sync_to_google_calendar(event_uuid, google_service)

# Reminders
await calendly.schedule_reminder(event_uuid, email, reminder_minutes_before=15)

# Analytics
stats = await calendly.get_event_statistics(user_uri, days=30)
```

#### 5.2 Endpoints (1 hour)
```python
POST   /api/v1/platforms/calendly/webhooks/events
POST   /api/v1/platforms/calendly/config
GET    /api/v1/platforms/calendly/events
```

#### 5.3 Google Calendar Integration (30 minutes)
- Install google-auth-oauthlib
- Implement sync_to_google_calendar()

### Phase 6: Slack (4 hours)

#### 6.1 Bot Setup (1 hour)
- Create Slack app on api.slack.com
- Configure OAuth scopes: chat:write, commands, app_mentions, im:history
- Set up slash commands

#### 6.2 Implementation (2 hours)
```python
from app.core.integrations.slack_automation import SlackAutomation

slack = SlackAutomation(
    team_id="T123456",
    bot_token="xoxb-...",
    signing_secret="signing_secret",
    webhook_url="https://hooks.slack.com/..."
)

# Command handling
response = await slack.handle_slash_command("status", user_id, channel_id)

# Alerts
await slack.send_alert(channel_id, "New Order", message, level="info", data={...})
await slack.send_order_alert(channel_id, order_data)
await slack.send_payment_confirmation(channel_id, order_id, amount)
await slack.send_shipment_notification(channel_id, order_id, tracking)

# OAuth
auth_result = await slack.handle_oauth_callback(code)

# User/channel info
user = await slack.get_user_info(user_id)
channel = await slack.get_channel_info(channel_id)
```

#### 6.3 Endpoints (1 hour)
```python
POST   /api/v1/platforms/slack/commands
POST   /api/v1/platforms/slack/events
POST   /api/v1/platforms/slack/alerts
```

### Phase 7: Telegram (4 hours)

#### 7.1 Bot Setup (30 minutes)
- Get bot token from @BotFather
- Set up webhook or polling

#### 7.2 Implementation (2 hours)
```python
from app.core.integrations.telegram_automation import TelegramAutomation

tg = TelegramAutomation(
    bot_token="1234567890:ABCDefgh...",
    webhook_url="https://yourdomain.com/tg/webhook",
    webhook_secret="secret_token"
)

# Webhook
await tg.set_webhook(webhook_url)

# Update handling
await tg.handle_update(update)

# Commands
await tg.handle_command("status", chat_id, user)

# Messages
await tg.send_message(chat_id, "Hello!", reply_markup=keyboard)
await tg.send_notification(chat_id, "Order Update", message, data={...})
await tg.send_order_notification(chat_id, order_id, status)
await tg.send_payment_notification(chat_id, amount, order_id)

# Polling (fallback)
updates = await tg.poll_updates(last_update_id)

# Bot management
await tg.set_commands([
    {"command": "start", "description": "Welcome"},
    {"command": "status", "description": "Check status"}
])
```

#### 7.3 Endpoints (1 hour)
```python
POST   /api/v1/platforms/telegram/webhooks/updates
POST   /api/v1/platforms/telegram/config
POST   /api/v1/platforms/telegram/send-notification
```

#### 7.4 Testing (30 minutes)
- Test webhook updates
- Verify message delivery
- Test polling fallback

---

## Common Implementation Patterns

### 1. Webhook Handling

**Pattern:** Signature verification → Parse payload → Route to handler → Store in DB

```python
async def handle_webhook(self, payload: Dict, signature: str, secret: str) -> bool:
    # 1. Verify signature
    if not self.verify_signature(payload, signature, secret):
        return False
    
    # 2. Parse payload
    event_type = payload.get("event_type")
    event_data = payload.get("data")
    
    # 3. Route to handler
    if event_type == "order.created":
        await self._handle_order_created(event_data)
    elif event_type == "order.updated":
        await self._handle_order_updated(event_data)
    
    # 4. Store webhook in DB
    await db.create(PlatformWebhookEvent, {
        "platform_type": self.platform_type,
        "event_type": event_type,
        "payload": event_data,
        "processed": True,
    })
    
    return True
```

### 2. Product Sync

**Pattern:** Fetch remote → Compare local → Create/update → Update DB

```python
async def sync_products(self, local_products: List[Dict]) -> Dict:
    remote_products = await self.fetch_remote_products()
    
    created_count = 0
    updated_count = 0
    
    for product in local_products:
        remote = await self._find_by_sku(product["sku"])
        
        if remote:
            # Update
            await self._update_remote(remote["id"], product)
            updated_count += 1
        else:
            # Create
            await self._create_remote(product)
            created_count += 1
    
    return {
        "created": created_count,
        "updated": updated_count,
        "total": len(local_products),
    }
```

### 3. Rate Limiting

**Pattern:** Track quota → Implement exponential backoff → Queue retries

```python
async def call_api(self, endpoint: str, payload: Dict) -> Dict:
    # Check rate limit
    quota = await self.check_rate_limit()
    if quota["remaining"] == 0:
        logger.warning("Rate limit reached, queuing request")
        await self.queue_retry(endpoint, payload)
        return {"status": "queued"}
    
    # Make request with exponential backoff
    max_retries = 3
    backoff = 1
    
    for attempt in range(max_retries):
        try:
            response = await self.http_client.post(endpoint, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(backoff)
                backoff *= 2
            else:
                raise
```

### 4. Error Handling & Logging

**Pattern:** Try-except → Log with correlation ID → Return standardized error

```python
async def process_order(self, order_id: str) -> Dict:
    correlation_id = str(uuid.uuid4())
    
    try:
        logger.info(f"[{correlation_id}] Processing order {order_id}")
        
        order = await self.get_order(order_id)
        if not order:
            raise ValueError(f"Order {order_id} not found")
        
        # Process order
        result = await self._confirm_order(order)
        
        logger.info(f"[{correlation_id}] Order processed successfully")
        return {"status": "success", "order_id": order_id}
        
    except Exception as e:
        logger.error(f"[{correlation_id}] Error: {e}", exc_info=True)
        return {
            "status": "error",
            "correlation_id": correlation_id,
            "message": str(e),
        }
```

---

## Environment Variables

Create `.env` file with platform credentials:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/sellia

# Facebook Shop
FACEBOOK_SHOP_APP_ID=xxx
FACEBOOK_SHOP_APP_SECRET=xxx
FACEBOOK_SHOP_WEBHOOK_TOKEN=xxx

# Instagram
INSTAGRAM_GRAPH_API_TOKEN=xxx
INSTAGRAM_WEBHOOK_TOKEN=xxx

# TikTok Shop
TIKTOK_CLIENT_ID=xxx
TIKTOK_CLIENT_SECRET=xxx
TIKTOK_WEBHOOK_SECRET=xxx

# Calendly
CALENDLY_API_TOKEN=xxx

# Slack
SLACK_CLIENT_ID=xxx
SLACK_CLIENT_SECRET=xxx
SLACK_SIGNING_SECRET=xxx

# Telegram
TELEGRAM_BOT_TOKEN=xxx
TELEGRAM_WEBHOOK_SECRET=xxx

# Google Calendar (for Calendly sync)
GOOGLE_CLIENT_ID=xxx
GOOGLE_CLIENT_SECRET=xxx
GOOGLE_REDIRECT_URI=http://localhost:8000/oauth/google/callback
```

---

## Testing Checklist

### Unit Tests
- [ ] Signature verification (all platforms)
- [ ] Payload parsing (all platforms)
- [ ] OAuth flows
- [ ] Rate limiting logic
- [ ] Credential encryption/decryption

### Integration Tests
- [ ] Webhook handling end-to-end
- [ ] Product sync bidirectional
- [ ] Order creation & status updates
- [ ] Inventory management
- [ ] Tracking updates

### Load Testing
- [ ] 1000 concurrent webhook handlers
- [ ] Rate limit enforcement
- [ ] Queue retry logic
- [ ] Database connection pooling

### Security Testing
- [ ] Signature verification bypass attempts
- [ ] SQL injection in search queries
- [ ] Unauthorized API access
- [ ] Credential exposure in logs

---

## Monitoring & Observability

### Logging Strategy

```python
logger.info(f"[{correlation_id}] {component}: {message}")
logger.warning(f"[{correlation_id}] {component}: {message}")
logger.error(f"[{correlation_id}] {component}: {message}", exc_info=True)
```

### Metrics to Track

1. **Webhook Processing:**
   - Requests/second per platform
   - Processing time (p50, p95, p99)
   - Success/failure rate

2. **Order Sync:**
   - Orders synced/hour per platform
   - Sync duration
   - Backlog size

3. **API Usage:**
   - Requests/minute per endpoint
   - Rate limit hits
   - Error rates

4. **Alerts:**
   - Webhook failures > 5 in 1 minute
   - Sync backlog > 100 orders
   - API error rate > 5%

---

## Deployment

### Docker Setup

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy app
COPY backend/ .

# Run
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Kubernetes Config

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sellia-platforms
spec:
  replicas: 3
  selector:
    matchLabels:
      app: sellia-platforms
  template:
    metadata:
      labels:
        app: sellia-platforms
    spec:
      containers:
      - name: app
        image: sellia:latest
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
        ports:
        - containerPort: 8000
        livenessProbe:
          httpGet:
            path: /api/v1/platforms/health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
```

---

## Rollback Strategy

If issues occur:

1. **Immediate rollback:**
   ```bash
   kubectl rollout undo deployment/sellia-platforms
   ```

2. **Feature flags** (disable problematic platform):
   ```python
   if config.PLATFORMS_ENABLED.get("tiktok_shop"):
       # Include TikTok endpoints
   ```

3. **Database migration rollback:**
   ```bash
   alembic downgrade -1
   ```

---

## Success Criteria

- ✅ All 6 platforms fully integrated
- ✅ Webhooks handling 100% of events
- ✅ Product sync completes within 5 minutes
- ✅ Order latency < 2 seconds
- ✅ 99.9% uptime
- ✅ Zero credential leaks
- ✅ All tests passing (unit + integration)
- ✅ Load testing passed (1000 concurrent)

---

## Next Steps

1. **Post-Integration:**
   - Set up monitoring dashboards
   - Configure alerting
   - Document API for frontend team
   - Create admin UI for platform management

2. **Advanced Features:**
   - Multi-channel inventory sync
   - Smart routing (order → best fulfillment)
   - Predictive analytics per platform
   - Custom webhook retry policies

3. **Scaling:**
   - Implement message queue (RabbitMQ/SQS)
   - Async processing for heavy operations
   - Caching layer (Redis)
   - Read replicas for analytics queries
