# Security & Data Isolation Integration Guide

This guide documents the production-grade security features implemented in SellIA. All features are designed to be drop-in compatible with the existing codebase.

## Features Implemented

### 1. Database Encryption (Data at Rest)

**Files**: `app/core/encryption.py` (updated), `app/core/database/security_models.py`

**Status**: Already exists in codebase

**What it does**:
- Encrypts sensitive fields using Fernet (symmetric encryption)
- API keys, credentials, and PII are encrypted before storage
- Decryption happens transparently in application code

**Setup**:
```python
from app.core.encryption import encrypt_value, decrypt_value

# In models that have sensitive data:
api_key_encrypted = encrypt_value(api_key)
api_key_decrypted = decrypt_value(api_key_encrypted)
```

**Environment variables**:
```bash
FERNET_SECRET=<32-byte base64 string>  # Generate: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
ENCRYPTION_KEY=<same as FERNET_SECRET>
```

---

### 2. Rate Limiting (DDoS + Brute Force Protection)

**Files**: `app/core/security/rate_limiter.py` (new)

**Thresholds**:
- Standard endpoints: 100 requests/minute
- Webhook endpoints: 1000 requests/minute  
- Login attempts: 5 failures → 15 min ban

**Usage in endpoints**:

```python
from fastapi import Request
from app.core.security import get_rate_limiter
from app.core.database import AsyncSessionLocal
import redis.asyncio as redis

@app.post("/api/v1/auth/login")
async def login(request: Request, credentials: LoginSchema):
    redis_client = redis.from_url(settings.REDIS_URL)
    limiter = get_rate_limiter(redis_client)
    
    # Check rate limit
    identifier = await limiter.get_client_identifier(request)
    result = await limiter.check_rate_limit(
        identifier,
        limit=100,
        window_seconds=60,
        endpoint_type="standard"
    )
    
    if not result["allowed"]:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Retry after {result['retry_after']} seconds"
        )
    
    # Check login brute force protection
    login_result = await limiter.check_login_attempt(identifier)
    if not login_result["allowed"]:
        raise HTTPException(
            status_code=429,
            detail=f"Too many failed attempts. Try again in {login_result['retry_after']} seconds"
        )
    
    # ... authentication logic
    
    if login_success:
        await limiter.clear_login_attempts(identifier)
    else:
        await limiter.record_failed_login(identifier)
```

**Environment variables**:
```bash
RATE_LIMIT_STANDARD_REQUESTS_PER_MIN=100
RATE_LIMIT_WEBHOOK_REQUESTS_PER_MIN=1000
RATE_LIMIT_LOGIN_MAX_ATTEMPTS=5
RATE_LIMIT_LOGIN_BAN_MINUTES=15
```

---

### 3. Audit Logging (Compliance & Forensics)

**Files**: `app/core/security/audit_logger.py` (new), `app/core/database/security_models.py`

**Tracked events**:
- Authentication (login, logout, password changes, 2FA)
- API access (all endpoints, methods, status codes)
- Data access (what fields, who, when)
- Financial operations (payments, refunds, subscriptions)
- Settings changes
- Admin actions
- Suspicious activity (risk scoring)

**Setup in database**:
```bash
# Run Alembic migration
alembic upgrade head
```

**Usage**:

```python
from app.core.security import get_audit_logger, AuditEventType
from app.core.database import AsyncSessionLocal

async def login(credentials: LoginSchema):
    audit_logger = get_audit_logger()
    
    # ... auth logic ...
    
    if login_success:
        await audit_logger.log_event(
            db=db_session,
            seller_id=user.seller_id,
            event_type=AuditEventType.LOGIN_SUCCESS,
            action="POST",
            user_id=user.id,
            resource_type="auth",
            ip_address=request.client.host,
            status="success",
            status_code=200,
        )
    else:
        await audit_logger.log_event(
            db=db_session,
            seller_id=user.seller_id,
            event_type=AuditEventType.LOGIN_FAILURE,
            action="POST",
            user_id=user.id,
            resource_type="auth",
            ip_address=request.client.host,
            status="failure",
            status_code=401,
            details={"reason": "invalid_password"}
        )
```

**Query audit logs**:
```python
audit_logger = get_audit_logger()
events, total = await audit_logger.get_events(
    db=db_session,
    seller_id=seller_id,
    event_type="login_success",
    start_date=datetime.now() - timedelta(days=7),
    limit=100,
)
```

**Cleanup (run periodically, e.g., daily Celery task)**:
```python
# In tasks/celery_app.py
from app.core.security import get_audit_logger

@celery_app.task(name="cleanup_audit_logs")
def cleanup_audit_logs():
    audit_logger = get_audit_logger()
    with SessionLocal() as db:
        deleted = asyncio.run(audit_logger.cleanup_expired_logs(db))
        logger.info(f"Deleted {deleted} expired audit logs")
```

**Environment variables**:
```bash
AUDIT_LOG_RETENTION_DAYS=90
```

---

### 4. Two-Factor Authentication (TOTP)

**Files**: `app/core/security/auth_factors.py` (new), `app/core/database/security_models.py`

**Features**:
- TOTP (Time-based One-Time Password) via authenticator apps
- QR code provisioning for easy setup
- 10 backup codes (one-time use)
- Failed attempt tracking

**Setup in database**:
```bash
alembic upgrade head
```

**Usage - Setup**:

```python
from app.core.security import get_auth_2fa_service

@app.post("/api/v1/auth/2fa/setup")
async def setup_2fa(current_user: User = Depends(get_current_user)):
    service = get_auth_2fa_service()
    
    secret, qr_code_url, backup_codes = await service.setup_totp(
        db=db_session,
        seller_id=current_user.seller_id,
        user_id=current_user.id,
        name=current_user.email,
    )
    
    return {
        "secret": secret,
        "qr_code_url": qr_code_url,  # Show in frontend for scanning
        "backup_codes": backup_codes,  # Show once for user to save
    }
```

**Verify setup (user scans QR and enters code)**:

```python
@app.post("/api/v1/auth/2fa/verify")
async def verify_2fa_setup(
    code: str,
    current_user: User = Depends(get_current_user)
):
    service = get_auth_2fa_service()
    
    is_valid, error = await service.verify_totp(
        db=db_session,
        seller_id=current_user.seller_id,
        user_id=current_user.id,
        code=code,
    )
    
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)
    
    return {"message": "2FA enabled successfully"}
```

**Login flow with 2FA**:

```python
@app.post("/api/v1/auth/login")
async def login_step1(credentials: LoginSchema):
    # ... verify username/password ...
    
    # Check if 2FA is enabled
    totp_2fa = db_session.query(TOTP2FA).filter(
        TOTP2FA.user_id == user.id,
        TOTP2FA.is_enabled == True
    ).first()
    
    if totp_2fa:
        # Return temp token for 2FA verification (expires in 5 min)
        temp_token = create_access_token({"sub": user.id, "type": "2fa_required"}, expires_delta=5)
        return {"requires_2fa": True, "temp_token": temp_token}
    
    # No 2FA, return full auth token
    return {"access_token": create_access_token({"sub": user.id})}


@app.post("/api/v1/auth/2fa/verify-login")
async def verify_2fa_login(code: str, temp_token: str):
    # Verify temp token
    payload = verify_token(temp_token)
    if payload.get("type") != "2fa_required":
        raise HTTPException(status_code=401, detail="Invalid request")
    
    user_id = payload.get("sub")
    
    service = get_auth_2fa_service()
    is_valid, error = await service.verify_totp_login(
        db=db_session,
        seller_id=...,
        user_id=user_id,
        code=code,
    )
    
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)
    
    # Return full auth token
    return {"access_token": create_access_token({"sub": user_id})}
```

---

### 5. API Key Management with Rotation

**Files**: `app/core/security/auth_factors.py` (new), `app/core/database/security_models.py`

**Features**:
- Generate API keys with 30-day default expiration
- Automatic key rotation with notification
- Scope-based access control
- Rate limiting per key
- Key revocation

**Usage**:

```python
from app.core.security import get_api_key_service

# Generate new API key
@app.post("/api/v1/users/api-keys")
async def create_api_key(
    name: str,
    current_user: User = Depends(get_current_user)
):
    service = get_api_key_service()
    
    key = await service.generate_api_key(
        db=db_session,
        seller_id=current_user.seller_id,
        user_id=current_user.id,
        name=name,
        scopes=["*"],  # Or specific scopes
        expires_in_days=30,
    )
    
    return {
        "key": key,  # Only shown once!
        "message": "Save this key somewhere secure. You won't be able to see it again."
    }


# Verify API key in middleware or endpoint guard
@app.get("/api/v1/orders")
async def get_orders(
    request: Request,
    current_user: User = Depends(get_current_user_or_api_key)
):
    # If using API key auth, extract it first
    service = get_api_key_service()
    api_key, error = await service.verify_api_key(
        db=db_session,
        seller_id=current_user.seller_id,
        key=request.headers.get("Authorization", "").replace("Bearer ", ""),
        ip_address=request.client.host,
    )
    
    if error:
        raise HTTPException(status_code=401, detail=error)
    
    # ... return orders ...


# List API keys
@app.get("/api/v1/users/api-keys")
async def list_api_keys(current_user: User = Depends(get_current_user)):
    service = get_api_key_service()
    keys = await service.list_api_keys(
        db=db_session,
        seller_id=current_user.seller_id,
        include_inactive=False,
    )
    
    return [
        {
            "id": k.id,
            "name": k.name,
            "prefix": k.key_prefix,
            "created_at": k.created_at,
            "expires_at": k.expires_at,
            "last_used": k.last_used_at,
        }
        for k in keys
    ]


# Rotate API key
@app.post("/api/v1/users/api-keys/{key_id}/rotate")
async def rotate_api_key(
    key_id: str,
    current_user: User = Depends(get_current_user)
):
    service = get_api_key_service()
    
    new_key, error = await service.rotate_api_key(
        db=db_session,
        seller_id=current_user.seller_id,
        key_id=key_id,
        user_id=current_user.id,
    )
    
    if error:
        raise HTTPException(status_code=400, detail=error)
    
    return {
        "new_key": new_key,
        "message": "Old key has been deactivated. Save the new key."
    }


# Revoke API key
@app.delete("/api/v1/users/api-keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    current_user: User = Depends(get_current_user)
):
    service = get_api_key_service()
    
    success, error = await service.revoke_api_key(
        db=db_session,
        seller_id=current_user.seller_id,
        key_id=key_id,
        user_id=current_user.id,
        reason="user_revoked",
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=error)
    
    return {"message": "API key revoked"}
```

---

### 6. Per-User Data Isolation (Row-Level Security)

**Files**: `app/core/security/data_isolation.py` (new)

**What it does**:
- Enforces `seller_id` filtering on all queries
- Prevents users from accessing other users' data
- Multi-tenant safety

**Usage**:

```python
from app.core.security import DataIsolationService, DataIsolationError, get_seller_context
from fastapi import Depends

# Get seller context from current user
async def get_seller_context_dep(
    current_user: User = Depends(get_current_user)
) -> SellerContext:
    return SellerContext(seller_id=current_user.seller_id, user_id=current_user.id)


# In endpoint - automatically filter by seller_id
@app.get("/api/v1/orders")
async def get_orders(
    seller_context: SellerContext = Depends(get_seller_context_dep),
    db: Session = Depends(get_db)
):
    # All queries automatically filtered by seller_id
    query = db.query(Order)
    query = DataIsolationService.enforce_seller_id(
        query,
        Order,
        seller_context.seller_id
    )
    
    orders = query.all()
    return orders


# Verify ownership before returning object
@app.get("/api/v1/orders/{order_id}")
async def get_order(
    order_id: str,
    seller_context: SellerContext = Depends(get_seller_context_dep),
    db: Session = Depends(get_db)
):
    order = db.query(Order).filter(Order.id == order_id).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # This will raise DataIsolationError if order doesn't belong to seller
    try:
        DataIsolationService.check_seller_id(order, seller_context.seller_id)
    except DataIsolationError as e:
        raise HTTPException(status_code=403, detail=str(e))
    
    return order
```

**Environment variables**: None required (uses seller_id from user model)

---

## CORS & CSRF Protection

**Files**: `app/main.py` (already configured), `app/middleware/csrf.py`

**CORS**:
```python
# In main.py - only allow frontend domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],  # e.g., https://selleia.com
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "X-CSRF-Token"],
)
```

**CSRF**:
```bash
# Enable in production
export CSRF_ENABLED=true
```

**Environment variables**:
```bash
FRONTEND_URL=https://selleia.com
CSRF_ENABLED=false  # Set to true in production
CSRF_TOKEN_EXPIRATION_HOURS=24
```

---

## SQL Injection Prevention

**Already implemented** via SQLAlchemy ORM:
- All queries use parameterized queries
- No raw SQL concatenation
- Input validation in Pydantic models

**Do NOT use**:
```python
# ❌ DANGEROUS - DON'T DO THIS
query = f"SELECT * FROM orders WHERE id = {order_id}"
```

**Use instead**:
```python
# ✅ SAFE
order = db.query(Order).filter(Order.id == order_id).first()
```

---

## Database Migrations

**Add security models to Alembic**:

```bash
# Generate migration
cd backend
alembic revision --autogenerate -m "Add security models (audit logs, 2FA, API keys)"

# Review the migration file in alembic/versions/

# Apply migration
alembic upgrade head
```

**Migration file should include**:
- `audit_logs` table
- `totp_2fa` table
- `api_keys` table

---

## Monitoring & Alerts

**Real-time logging**:
```python
# Structured logging to ELK/DataDog
logger = logging.getLogger("audit")
logger.warning("Suspicious login attempt", extra={
    "user_id": "user_123",
    "ip": "192.168.1.1",
    "failed_attempts": 3,
})
```

**Dashboards to create**:
1. Failed login attempts (by IP, user)
2. Rate limit violations
3. API key expiration tracking
4. Data isolation violations (CRITICAL)
5. Suspicious activity (risk score > 70)

---

## Testing

**Run security tests**:

```bash
cd backend
pip install pytest pytest-asyncio pytest-cov

# Run all security tests
pytest tests/test_security.py -v

# Run with coverage
pytest tests/test_security.py --cov=app.core.security --cov-report=html

# Run specific test
pytest tests/test_security.py::test_rate_limiter_block_requests -v
```

---

## Production Checklist

Before deploying to production:

- [ ] Generate strong `SECRET_KEY` (32+ chars)
- [ ] Generate `FERNET_SECRET` key
- [ ] Set `ENVIRONMENT=production`
- [ ] Enable `CSRF_ENABLED=true`
- [ ] Configure Cloudflare DDoS protection
- [ ] Set up database backups
- [ ] Enable audit log retention (default 90 days)
- [ ] Configure email notifications for security events
- [ ] Set up monitoring/alerts for rate limit violations
- [ ] Enable 2FA for all admin accounts
- [ ] Rotate API keys on schedule (30-day default)
- [ ] Run audit log cleanup job (daily)
- [ ] Test data isolation in production (verify cross-tenant blocks)
- [ ] Monitor for data isolation violations
- [ ] Set up log shipping to ELK/Datadog

---

## Troubleshooting

**Rate limit false positives?**
- Increase limits in `.env` if needed
- Check X-Forwarded-For header for proper IP detection
- Whitelist trusted IPs in load balancer config

**2FA setup failing?**
- Ensure Redis is running (for session storage)
- Check system clock is synced (TOTP is time-sensitive)
- User's authenticator app should be synced

**API key expiration issues?**
- Check system timezone is UTC
- Verify expires_at calculation
- Schedule automatic rotation reminders

**Data isolation violations?**
- Check seller_id is correctly set on all objects
- Verify DataIsolationService.enforce_seller_id() called on all queries
- Review audit logs for pattern analysis

---

## References

- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
- [Fernet (cryptography.io)](https://cryptography.io/en/latest/fernet/)
- [TOTP RFC 6238](https://tools.ietf.org/html/rfc6238)
- [Rate Limiting Best Practices](https://cloud.google.com/architecture/rate-limiting-strategies-techniques)
