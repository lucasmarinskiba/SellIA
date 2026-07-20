# Platforms Integration - Quick Reference Guide

Fast lookup for developers implementing platform features.

---

## Database Tables Quick Lookup

### Facebook Shop
```sql
-- Main integration
SELECT * FROM facebook_shops WHERE account_id = 'acc_123';

-- Products
SELECT * FROM facebook_products WHERE shop_id = 'fb_shop_123';

-- Orders
SELECT * FROM facebook_orders WHERE shop_id = 'fb_shop_123' AND status = 'PENDING';
```

### Instagram Shop
```sql
SELECT * FROM instagram_shops WHERE account_id = 'acc_123';
SELECT * FROM instagram_products WHERE shop_id = 'ig_shop_123';
SELECT * FROM instagram_orders WHERE status = 'PAYMENT_PENDING' LIMIT 10;
```

### TikTok Shop
```sql
SELECT * FROM tiktok_shops WHERE account_id = 'acc_123';
SELECT * FROM tiktok_orders WHERE shop_id = 'tt_shop_123' ORDER BY created_at DESC;
```

### Calendly
```sql
SELECT * FROM calendly_accounts WHERE account_id = 'acc_123';
SELECT * FROM calendly_events WHERE account_id = 'cal_acc_123' AND status = 'scheduled';
```

### Slack
```sql
SELECT * FROM slack_workspaces WHERE account_id = 'acc_123';
SELECT * FROM slack_commands WHERE workspace_id = 'ws_123' ORDER BY executed_at DESC;
```

### Telegram
```sql
SELECT * FROM telegram_bots WHERE account_id = 'acc_123';
SELECT * FROM telegram_users WHERE bot_id = 'bot_123' AND status = 'active';
SELECT * FROM telegram_messages WHERE bot_id = 'bot_123' ORDER BY sent_at DESC;
```

---

## API Endpoints Cheat Sheet

### Facebook Shop
```
POST   /api/v1/platforms/facebook-shop/webhooks/orders
       Header: account_id, X-Hub-Signature
       
POST   /api/v1/platforms/facebook-shop/config
       Body: {platform_type, api_key, webhook_url, is_active, metadata}
       
POST   /api/v1/platforms/facebook-shop/sync/products
       Body: {platform_type, force_refresh, page, limit}
       
GET    /api/v1/platforms/facebook-shop/orders/{order_id}
       Header: account_id
```

### Instagram Shop
```
POST   /api/v1/platforms/instagram-shop/webhooks/orders
       Header: account_id, X-Hub-Signature
       
POST   /api/v1/platforms/instagram-shop/sync/products
       Body: {platform_type, force_refresh, page, limit}
       
GET    /api/v1/platforms/instagram-shop/analytics
       Header: account_id
       Query: days=30
```

### TikTok Shop
```
POST   /api/v1/platforms/tiktok-shop/webhooks/orders
       Header: account_id
       
POST   /api/v1/platforms/tiktok-shop/config
       Body: {platform_type, api_key, webhook_url}
       
POST   /api/v1/platforms/tiktok-shop/sync/orders
       Body: {platform_type, force_refresh, page, limit}
```

### Calendly
```
POST   /api/v1/platforms/calendly/webhooks/events
       Body: {event: "invitee.created"|"invitee.canceled", payload: {...}}
       
POST   /api/v1/platforms/calendly/config
       Body: {platform_type, api_key, webhook_url}
       
GET    /api/v1/platforms/calendly/events
       Header: account_id
       Query: days=7
```

### Slack
```
POST   /api/v1/platforms/slack/commands
       Body: {token, command, text, user_id, channel_id}
       
POST   /api/v1/platforms/slack/events
       Body: {token, challenge, event: {...}}
       
POST   /api/v1/platforms/slack/alerts
       Header: account_id
       Body: {title, message, level, data}
```

### Telegram
```
POST   /api/v1/platforms/telegram/webhooks/updates
       Header: account_id
       Body: {update_id, message: {...}, callback_query: {...}}
       
POST   /api/v1/platforms/telegram/config
       Body: {platform_type, api_key, webhook_url, webhook_secret}
       
POST   /api/v1/platforms/telegram/send-notification
       Header: account_id
       Body: {title, message, level, data}
```

### Global
```
GET    /api/v1/platforms/health
       → {status, platforms: {...}, timestamp}
       
GET    /api/v1/platforms/status
       Header: account_id
       → {account_id, platforms: {...}}
```

---

## Common Code Snippets

### Initialize Platform
```python
from app.core.integrations.facebook_shop_automation import FacebookShopAutomation

# Get credentials from DB
shop = await db.query(FacebookShop).filter_by(account_id=account_id).first()

# Initialize
fb = FacebookShopAutomation(
    shop_id=shop.shop_id,
    access_token=shop.access_token,  # Should be decrypted
    webhook_verify_token=shop.webhook_verify_token,
    catalog_id=shop.catalog_id,
)
```

### Handle Webhook
```python
@router.post("/webhooks")
async def handle_webhook(request: Request, account_id: str = Header(...)):
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature")
    
    # Verify
    if not fb.verify_webhook_signature(body, signature):
        raise HTTPException(status_code=403, detail="Invalid signature")
    
    # Parse
    payload = await request.json()
    
    # Process
    result = await fb.handle_webhook(payload)
    
    # Log
    await db.create(PlatformWebhookEvent, {
        "account_id": account_id,
        "platform_type": "facebook_shop",
        "event_type": "order",
        "payload": payload,
        "processed": True,
    })
    
    return {"status": "success"}
```

### Sync Products
```python
# Fetch from platform
remote_products = await fb.sync_products_from_facebook()

# Convert to local format
local_products = [
    {
        "name": p["name"],
        "price": float(p["price"]) / 100,
        "sku": p["sku"],
        "description": p.get("description", ""),
        "images": p.get("images", []),
    }
    for p in remote_products
]

# Save to DB
for product in local_products:
    await db.create(FacebookProduct, {
        "shop_id": shop_id,
        "facebook_product_id": product["id"],
        **product,
    })
```

### Send Alert via Slack
```python
slack = SlackAutomation(
    team_id=workspace.team_id,
    bot_token=workspace.bot_access_token,
    signing_secret=workspace.webhook_url,
)

await slack.send_alert(
    channel_id="C123456",
    title="New Order",
    message="Order #12345 from John Doe",
    level=SlackAlertLevel.INFO,
    data={
        "Amount": "$99.99",
        "Email": "john@example.com",
    }
)
```

### Send Telegram Notification
```python
tg = TelegramAutomation(bot_token=bot.bot_token)

await tg.send_notification(
    chat_id=user.telegram_user_id,
    title="Order Status",
    message="Your order #12345 has been shipped!",
    data={
        "Tracking": "1Z999AA10123456784",
        "Carrier": "FedEx",
    }
)
```

---

## Error Codes & Messages

### Webhook Errors
| Code | Cause | Solution |
|------|-------|----------|
| 403 | Invalid signature | Verify webhook secret |
| 400 | Malformed payload | Check platform API docs for format |
| 500 | Processing error | Check logs with correlation ID |
| 429 | Rate limited | Implement backoff, check quota |

### Config Errors
| Code | Cause | Solution |
|------|-------|----------|
| 400 | Invalid API key | Test key in platform console |
| 401 | Unauthorized | Refresh OAuth tokens |
| 403 | Insufficient scopes | Re-authorize with required scopes |

### Sync Errors
| Code | Cause | Solution |
|------|-------|----------|
| 404 | Resource not found | Verify product/order IDs exist |
| 409 | Conflict | Check sync status, retry manually |
| 503 | Platform unavailable | Retry later (exponential backoff) |

---

## Debugging Tips

### Enable Verbose Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("app.core.integrations")
logger.setLevel(logging.DEBUG)
```

### Check Webhook Events
```sql
-- View all webhook events
SELECT * FROM platform_webhook_events 
WHERE account_id = 'acc_123' 
ORDER BY created_at DESC 
LIMIT 20;

-- Find failed webhooks
SELECT * FROM platform_webhook_events 
WHERE processed = FALSE 
AND created_at > NOW() - INTERVAL '1 hour';

-- Check retry count
SELECT COUNT(*) as retry_count, event_type
FROM platform_webhook_events
WHERE retry_count > 0
GROUP BY event_type;
```

### Verify Credentials
```python
# Test API connection
fb = FacebookShopAutomation(shop_id, token, verify_token, catalog_id)

# Get shop info to verify token works
try:
    shops = await fb.sync_products_from_facebook(limit=1)
    print("✅ Credentials valid")
except httpx.HTTPError as e:
    print(f"❌ Credentials error: {e}")
```

### Check Rate Limits
```sql
SELECT * FROM platform_rate_limits 
WHERE account_id = 'acc_123' 
AND reset_at > NOW();

-- Check if approaching limit
SELECT *, (requests_limit - requests_made) as remaining
FROM platform_rate_limits
WHERE remaining < 10;
```

### Monitor Sync Status
```sql
SELECT * FROM platform_sync_status
WHERE account_id = 'acc_123'
ORDER BY updated_at DESC;

-- Check for stuck syncs
SELECT * FROM platform_sync_status
WHERE status = 'syncing'
AND updated_at < NOW() - INTERVAL '1 hour';
```

---

## Performance Optimization Checklist

- [ ] Use connection pooling (httpx.AsyncClient)
- [ ] Index foreign keys (shop_id, account_id)
- [ ] Index status columns for queries
- [ ] Implement request caching for product lists
- [ ] Use batch operations for bulk inserts
- [ ] Implement pagination for large result sets
- [ ] Monitor query performance with EXPLAIN
- [ ] Use database transaction for atomic operations

---

## Security Checklist

- [ ] Never log credentials or tokens
- [ ] Encrypt credentials in database (use field_encryption.py)
- [ ] Verify webhook signatures before processing
- [ ] Validate timestamp in webhook (within 5 minutes)
- [ ] Use HTTPS for all webhook endpoints
- [ ] Implement rate limiting per account
- [ ] Sanitize error messages (no sensitive info)
- [ ] Rotate tokens regularly
- [ ] Use environment variables for secrets

---

## Testing Commands

### Test Facebook Webhook
```bash
curl -X POST http://localhost:8000/api/v1/platforms/facebook-shop/webhooks/orders \
  -H "Content-Type: application/json" \
  -H "account_id: acc_123" \
  -H "X-Hub-Signature: sha1=test" \
  -d '{"entry": [{"changes": [{"field": "orders", "value": {"id": "order_123", "order_status": "CREATED"}}]}]}'
```

### Test Slack Command
```bash
curl -X POST http://localhost:8000/api/v1/platforms/slack/commands \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "token=xoxb-xxx&command=/status&text=&user_id=U123&channel_id=C123"
```

### Test Telegram Update
```bash
curl -X POST http://localhost:8000/api/v1/platforms/telegram/webhooks/updates \
  -H "Content-Type: application/json" \
  -H "account_id: acc_123" \
  -d '{"update_id": 123, "message": {"message_id": 1, "from": {"id": 456}, "text": "/status"}}'
```

### Test Health
```bash
curl http://localhost:8000/api/v1/platforms/health
```

---

## Common Tasks

### How to: Manually Trigger Product Sync
```python
# In admin API or background task
facebook_shop = await db.query(FacebookShop).filter_by(account_id=account_id).first()
fb = FacebookShopAutomation(...)

products = await fb.sync_products_from_facebook()

# Save to DB
for product in products:
    existing = await db.query(FacebookProduct).filter_by(
        shop_id=facebook_shop.id,
        sku=product["sku"]
    ).first()
    
    if existing:
        # Update
        for key, val in product.items():
            setattr(existing, key, val)
        db.commit()
    else:
        # Create
        await db.create(FacebookProduct, {...product})
```

### How to: Resend Failed Order
```python
# Find failed order
order = await db.query(FacebookOrder).filter_by(
    id=order_id, 
    retry_count__lt=3
).first()

# Retry processing
success = await fb.confirm_order(order.facebook_order_id)

if success:
    order.retry_count = 0
    order.status = OrderStatus.CONFIRMED
else:
    order.retry_count += 1

db.commit()
```

### How to: Update Platform Config
```python
shop = await db.query(FacebookShop).filter_by(
    account_id=account_id
).first()

shop.access_token = encrypt(new_token)
shop.webhook_url = new_webhook_url
shop.updated_at = datetime.utcnow()

db.commit()
```

### How to: Enable/Disable Platform
```python
shop = await db.query(FacebookShop).filter_by(account_id=account_id).first()
shop.is_active = False
db.commit()

# Now webhooks won't be processed for this shop
```

---

## Environment Variables Template

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/sellia

# Encryption
ENCRYPTION_KEY=your-32-byte-base64-key

# Facebook
FACEBOOK_APP_ID=your_app_id
FACEBOOK_APP_SECRET=your_app_secret
FACEBOOK_WEBHOOK_TOKEN=your_verify_token

# Instagram
INSTAGRAM_BUSINESS_ACCOUNT_ID=your_account_id
INSTAGRAM_GRAPH_API_TOKEN=your_token

# TikTok
TIKTOK_CLIENT_ID=your_client_id
TIKTOK_CLIENT_SECRET=your_client_secret
TIKTOK_WEBHOOK_SECRET=your_webhook_secret

# Calendly
CALENDLY_API_TOKEN=your_token
GOOGLE_OAUTH_CREDENTIALS=path_to_credentials.json

# Slack
SLACK_CLIENT_ID=your_client_id
SLACK_CLIENT_SECRET=your_client_secret
SLACK_SIGNING_SECRET=your_signing_secret

# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_WEBHOOK_SECRET=your_webhook_secret

# Feature Flags
PLATFORMS_ENABLED={"facebook_shop": true, "instagram_shop": true, "tiktok_shop": true, "calendly": true, "slack": true, "telegram": true}
```

---

## Useful SQL Queries

### Find all connected platforms for account
```sql
SELECT 'facebook_shop' as platform, COUNT(*) as count FROM facebook_shops WHERE account_id = 'acc_123' UNION ALL
SELECT 'instagram_shop', COUNT(*) FROM instagram_shops WHERE account_id = 'acc_123' UNION ALL
SELECT 'tiktok_shop', COUNT(*) FROM tiktok_shops WHERE account_id = 'acc_123' UNION ALL
SELECT 'calendly', COUNT(*) FROM calendly_accounts WHERE account_id = 'acc_123' UNION ALL
SELECT 'slack', COUNT(*) FROM slack_workspaces WHERE account_id = 'acc_123' UNION ALL
SELECT 'telegram', COUNT(*) FROM telegram_bots WHERE account_id = 'acc_123';
```

### Orders needing attention
```sql
SELECT p.platform_type, COUNT(*) as count, o.status
FROM platform_webhook_events p
JOIN facebook_orders o ON p.payload->>'order_id' = o.facebook_order_id
WHERE p.account_id = 'acc_123' AND p.processed = FALSE
GROUP BY p.platform_type, o.status;
```

### Last sync status per platform
```sql
SELECT account_id, platform_type, sync_type, last_sync_at, status, error_message
FROM platform_sync_status
WHERE account_id = 'acc_123'
ORDER BY platform_type, sync_type;
```

### Rate limit usage
```sql
SELECT platform_type, endpoint, requests_made, requests_limit,
       ROUND(100.0 * requests_made / requests_limit, 2) as usage_percent,
       reset_at
FROM platform_rate_limits
WHERE account_id = 'acc_123'
ORDER BY usage_percent DESC;
```

---

Last Updated: 2026-06-30  
Quick Reference Version: 1.0
