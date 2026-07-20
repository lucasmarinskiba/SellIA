# Quick Start — Security Implementation

Minimal steps to integrate security features into your API endpoints.

## 1. Update Environment Variables

Copy `backend/.env.example` → `backend/.env`:

```bash
cp backend/.env.example backend/.env

# Edit .env with your settings:
FERNET_SECRET=<generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())">
ENCRYPTION_KEY=$FERNET_SECRET
```

## 2. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

New dependencies added:
- `pyotp` - TOTP
- `qrcode` - QR code generation
- `cryptography` - Fernet encryption
- `slowapi` - Rate limiting
- `redis` - Session storage

## 3. Run Database Migrations

```bash
# Generate migration
alembic revision --autogenerate -m "Add security tables"

# Review generated file
cat alembic/versions/*_add_security_tables.py

# Apply migration
alembic upgrade head

# Verify tables
psql -U ia_vendedor -d ia_vendedor -c "\dt audit_logs totp_2fa api_keys"
```

## 4. Add Rate Limiting to Endpoints

Simple example for login endpoint:

```python
from fastapi import Request, HTTPException, status
from app.core.security import get_rate_limiter
import redis.asyncio as redis

@app.post("/api/v1/auth/login")
async def login(request: Request, credentials: LoginSchema):
    # Initialize rate limiter
    redis_client = redis.from_url(settings.REDIS_URL)
    limiter = get_rate_limiter(redis_client)
    
    # Get client IP
    identifier = await limiter.get_client_identifier(request)
    
    # Check rate limit (100 req/min)
    result = await limiter.check_rate_limit(identifier, 100, 60)
    if not result["allowed"]:
        raise HTTPException(
            status_code=429,
            detail=f"Too many requests. Try again in {result['retry_after']} seconds"
        )
    
    # Check brute force protection
    login_check = await limiter.check_login_attempt(identifier)
    if not login_check["allowed"]:
        raise HTTPException(
            status_code=429,
            detail=f"Too many failed attempts. Try again in {login_check['retry_after']} seconds"
        )
    
    # Attempt login
    user = authenticate_user(credentials.email, credentials.password)
    if not user:
        await limiter.record_failed_login(identifier)
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Success
    await limiter.clear_login_attempts(identifier)
    return {"access_token": create_access_token({"sub": user.id})}
```

## 5. Add Audit Logging

Log important events:

```python
from app.core.security import get_audit_logger, AuditEventType
from app.core.database import AsyncSessionLocal

@app.post("/api/v1/auth/login")
async def login(request: Request, credentials: LoginSchema):
    # ... auth logic ...
    
    audit_logger = get_audit_logger()
    async with AsyncSessionLocal() as db:
        if login_success:
            await audit_logger.log_event(
                db=db,
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
                db=db,
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

## 6. Add Data Isolation

Filter all queries by seller_id:

```python
from app.core.security import DataIsolationService

@app.get("/api/v1/orders")
async def get_orders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Filter by seller_id
    query = db.query(Order)
    query = DataIsolationService.enforce_seller_id(
        query,
        Order,
        current_user.seller_id
    )
    
    orders = query.all()
    return orders


# For single resource, verify ownership
@app.get("/api/v1/orders/{order_id}")
async def get_order(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404)
    
    try:
        DataIsolationService.check_seller_id(order, current_user.seller_id)
    except DataIsolationError:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return order
```

## 7. Setup 2FA Endpoints (Optional)

```python
from app.core.security import get_auth_2fa_service

@app.post("/api/v1/auth/2fa/setup")
async def setup_2fa(current_user: User = Depends(get_current_user)):
    service = get_auth_2fa_service()
    
    secret, qr_code, backup_codes = await service.setup_totp(
        db=db_session,
        seller_id=current_user.seller_id,
        user_id=current_user.id,
    )
    
    return {
        "secret": secret,
        "qr_code": qr_code,  # Show in frontend
        "backup_codes": backup_codes,  # User saves these
    }

@app.post("/api/v1/auth/2fa/verify")
async def verify_2fa(code: str, current_user: User = Depends(get_current_user)):
    service = get_auth_2fa_service()
    
    is_valid, error = await service.verify_totp(
        db=db_session,
        seller_id=current_user.seller_id,
        user_id=current_user.id,
        code=code,
    )
    
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)
    
    return {"message": "2FA enabled"}
```

## 8. Setup API Key Endpoints (Optional)

```python
from app.core.security import get_api_key_service

@app.post("/api/v1/users/api-keys")
async def create_api_key(name: str, current_user: User = Depends(get_current_user)):
    service = get_api_key_service()
    
    key = await service.generate_api_key(
        db=db_session,
        seller_id=current_user.seller_id,
        user_id=current_user.id,
        name=name,
    )
    
    return {"key": key}

@app.get("/api/v1/users/api-keys")
async def list_api_keys(current_user: User = Depends(get_current_user)):
    service = get_api_key_service()
    
    keys = await service.list_api_keys(
        db=db_session,
        seller_id=current_user.seller_id,
    )
    
    return [{"id": k.id, "name": k.name, "prefix": k.key_prefix} for k in keys]
```

## 9. Test the Implementation

```bash
# Run security tests
pytest tests/test_security.py -v

# Test rate limiting
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test"}' \
  --repeat 150  # Should be blocked after 100 requests

# Test audit logging
psql -U ia_vendedor -d ia_vendedor -c \
  "SELECT event_type, status, COUNT(*) FROM audit_logs GROUP BY event_type, status"

# Test 2FA
curl -X POST http://localhost:8000/api/v1/auth/2fa/setup \
  -H "Authorization: Bearer $TOKEN"
```

## 10. Production Deployment

Before deploying:

1. **Generate secrets**
   ```bash
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

2. **Update .env.production**
   ```bash
   ENVIRONMENT=production
   CSRF_ENABLED=true
   FRONTEND_URL=https://yourdomain.com
   ```

3. **Run migrations**
   ```bash
   alembic upgrade head
   ```

4. **Enable monitoring**
   - Set up log aggregation (ELK, DataDog)
   - Configure alerts for security events
   - Set up dashboards

5. **Test end-to-end**
   - Rate limiting works
   - Audit logs recorded
   - Data isolation enforced
   - 2FA flow works

---

## Common Patterns

### Rate-Limited Endpoint

```python
async def rate_limited_endpoint(request: Request, db: Session):
    # Check rate limit
    limiter = get_rate_limiter(redis_client)
    result = await limiter.check_rate_limit(
        identifier, 100, 60
    )
    if not result["allowed"]:
        raise HTTPException(status_code=429)
    
    # ... endpoint logic ...
    
    # Log access
    audit_logger = get_audit_logger()
    await audit_logger.log_event(
        db=db,
        seller_id=seller_id,
        event_type=AuditEventType.API_CALL,
        action="GET",
        status="success",
    )
```

### Protected Resource

```python
async def protected_resource(
    resource_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Fetch resource
    resource = db.query(Resource).filter(Resource.id == resource_id).first()
    if not resource:
        raise HTTPException(status_code=404)
    
    # Verify ownership (data isolation)
    DataIsolationService.check_seller_id(resource, current_user.seller_id)
    
    # Log access
    audit_logger = get_audit_logger()
    await audit_logger.log_event(
        db=db,
        seller_id=current_user.seller_id,
        event_type=AuditEventType.DATA_READ,
        action="GET",
        resource_type=resource.__class__.__name__,
        resource_id=resource_id,
        data_accessed=["id", "name", "price"],  # Fields accessed
    )
    
    return resource
```

### Administrative Action with Audit

```python
async def admin_action(
    action: str,
    target_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Verify admin (should be in middleware/guard)
    if not current_user.is_admin:
        raise HTTPException(status_code=403)
    
    # Perform action
    target = db.query(User).filter(User.id == target_id).first()
    if not target:
        raise HTTPException(status_code=404)
    
    # ... modify target ...
    
    # Log admin action
    audit_logger = get_audit_logger()
    await audit_logger.log_event(
        db=db,
        seller_id=current_user.seller_id,
        event_type=AuditEventType.ADMIN_ACTION,
        action="PUT",
        user_id=current_user.id,
        resource_type="user",
        resource_id=target_id,
        details={"action": action, "changes": {...}},
    )
```

---

## Troubleshooting

**Rate limiting not working?**
- Ensure Redis is running: `redis-cli ping`
- Check `REDIS_URL` in `.env`

**2FA code invalid?**
- User's authenticator app clock must be synced
- TOTP has 30-second window tolerance
- Check server time: `date -u`

**Audit logs not appearing?**
- Verify migration ran: `psql ... -c "\dt audit_logs"`
- Check `get_audit_logger()` is called
- Review logs for DB errors

**Data isolation not working?**
- Ensure `seller_id` is set on all objects
- Verify `DataIsolationService.enforce_seller_id()` called on all queries
- Check audit logs for violations (should be CRITICAL)

---

## Next Steps

1. See `SECURITY_INTEGRATION.md` for detailed integration guide
2. See `SECURITY_FEATURES.md` for architecture & design details
3. See `MIGRATION_INSTRUCTIONS.md` for database setup
4. Run `pytest tests/test_security.py` to validate implementation
