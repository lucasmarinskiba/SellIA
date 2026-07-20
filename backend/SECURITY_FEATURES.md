# SellIA Security & Data Isolation — Complete Implementation

## Overview

This implementation provides production-grade security covering:

1. **Database Encryption** - Sensitive data encrypted at rest
2. **Rate Limiting** - DDoS & brute-force protection
3. **Audit Logging** - Complete compliance trail (90-day retention)
4. **Two-Factor Authentication** - TOTP via authenticator apps
5. **API Key Management** - Secure key generation with rotation
6. **Per-User Data Isolation** - Row-level security for multi-tenant safety
7. **CORS/CSRF Protection** - Already configured
8. **SQL Injection Prevention** - ORM-based parameterized queries

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   FastAPI Application                    │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────────────────────────────────────────┐   │
│  │            Request Processing Pipeline            │   │
│  ├──────────────────────────────────────────────────┤   │
│  │  1. Rate Limiter      (check against Redis)      │   │
│  │  2. Threat Intel      (IP reputation, VPN)       │   │
│  │  3. Data Isolation    (enforce seller_id)        │   │
│  │  4. Authentication   (JWT + 2FA)                 │   │
│  │  5. Audit Logging    (log to database)           │   │
│  └──────────────────────────────────────────────────┘   │
│                           ↓                              │
│  ┌──────────────────────────────────────────────────┐   │
│  │          Core Security Services                   │   │
│  ├──────────────────────────────────────────────────┤   │
│  │  • RateLimiter     (Redis-backed)                │   │
│  │  • AuditLogger     (DB-backed)                   │   │
│  │  • Auth2FAService  (TOTP)                        │   │
│  │  • APIKeyService   (Key generation & rotation)   │   │
│  │  • DataIsolationSvc (RLS enforcement)            │   │
│  └──────────────────────────────────────────────────┘   │
│                           ↓                              │
│  ┌──────────────────────────────────────────────────┐   │
│  │          Encryption Layer                         │   │
│  ├──────────────────────────────────────────────────┤   │
│  │  • Fernet (symmetric)  - API keys, credentials   │   │
│  │  • Database - Encrypted columns in Payment       │   │
│  │  • HTTPS/TLS - Transport layer (Cloudflare)      │   │
│  └──────────────────────────────────────────────────┘   │
│                           ↓                              │
│  ┌──────────────────────────────────────────────────┐   │
│  │          Data Storage                             │   │
│  ├──────────────────────────────────────────────────┤   │
│  │  • PostgreSQL        (primary data)              │   │
│  │  • Redis             (rate limiting, cache)      │   │
│  │  • Audit Logs (DB)   (security events)           │   │
│  └──────────────────────────────────────────────────┘   │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

---

## Files Added/Modified

### New Files

```
backend/app/core/security/
├── __init__.py                    # Package exports
├── rate_limiter.py               # DDoS + brute-force protection
├── audit_logger.py               # Audit logging service
├── auth_factors.py               # 2FA + API key management
└── data_isolation.py             # Row-level security

backend/app/core/database/
└── security_models.py            # ORM models for Alembic migration

backend/tests/
└── test_security.py              # Comprehensive security tests

backend/
├── SECURITY_INTEGRATION.md       # Integration guide
└── SECURITY_FEATURES.md          # This file
```

### Modified Files

```
backend/
├── requirements.txt              # Added: pyotp, qrcode, slowapi, redis
├── .env.example                  # Added: security env vars
└── app/core/database/payment_models.py
                                  # Added: encrypted billing fields
```

---

## Database Schema

### `audit_logs` Table

```sql
CREATE TABLE audit_logs (
    id VARCHAR(50) PRIMARY KEY,
    seller_id VARCHAR(255) NOT NULL,        -- Multi-tenant filtering
    user_id VARCHAR(255),                   -- Who performed action
    event_type VARCHAR(50) NOT NULL,        -- login_success, data_read, etc
    resource_type VARCHAR(50),              -- orders, users, settings, etc
    resource_id VARCHAR(255),               -- Specific resource ID
    action VARCHAR(100) NOT NULL,           -- GET, POST, DELETE, etc
    status VARCHAR(20) NOT NULL,            -- success, failure, pending
    status_code INTEGER,                    -- HTTP status
    ip_address VARCHAR(50),                 -- Client IP
    user_agent VARCHAR(500),                -- Browser/client info
    request_id VARCHAR(50),                 -- Correlation ID
    message TEXT,                           -- Human-readable message
    details JSON,                           -- Structured context
    error_details JSON,                     -- Error info if failed
    data_accessed JSON,                     -- Fields read (for PII audit)
    data_modified JSON,                     -- Fields changed
    rows_affected INTEGER,                  -- Number of rows touched
    is_risk BOOLEAN DEFAULT FALSE,          -- Suspicious activity flag
    risk_score INTEGER,                     -- 0-100 risk score
    risk_reason VARCHAR(255),               -- Why flagged
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP,                   -- Auto-delete after 90 days
    
    INDEX idx_seller_id (seller_id),
    INDEX idx_event_type (event_type),
    INDEX idx_created_at (created_at),
    INDEX idx_seller_event_date (seller_id, event_type, created_at)
);
```

### `totp_2fa` Table

```sql
CREATE TABLE totp_2fa (
    id VARCHAR(50) PRIMARY KEY,
    seller_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    secret VARCHAR(32) NOT NULL,           -- Base32 TOTP secret
    provisioning_uri VARCHAR(255),         -- QR code URI
    backup_codes JSON,                     -- Hashed backup codes
    backup_codes_used JSON DEFAULT '[]',   -- Used backup codes
    is_enabled BOOLEAN DEFAULT FALSE,
    is_verified BOOLEAN DEFAULT FALSE,
    verified_at TIMESTAMP,
    last_used_at TIMESTAMP,
    failed_attempts INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE KEY uq_seller_user (seller_id, user_id),
    INDEX idx_seller_id (seller_id),
    INDEX idx_user_id (user_id)
);
```

### `api_keys` Table

```sql
CREATE TABLE api_keys (
    id VARCHAR(50) PRIMARY KEY,
    seller_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    key_hash VARCHAR(64) NOT NULL UNIQUE,  -- SHA256(full_key)
    key_prefix VARCHAR(20) NOT NULL,       -- sk_live_abc123...
    key_encrypted VARCHAR(500) NOT NULL,   -- Encrypted full key
    name VARCHAR(255) NOT NULL,
    description VARCHAR(500),
    scopes JSON DEFAULT '[]',
    is_active BOOLEAN DEFAULT TRUE,
    is_rotated BOOLEAN DEFAULT FALSE,
    rate_limit_per_min INTEGER DEFAULT 60,
    last_used_at TIMESTAMP,
    last_used_ip VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    rotation_scheduled_at TIMESTAMP,
    rotated_at TIMESTAMP,
    created_by VARCHAR(255),
    revoked_at TIMESTAMP,
    revoked_by VARCHAR(255),
    revoke_reason VARCHAR(255),
    
    INDEX idx_seller_id (seller_id),
    INDEX idx_user_id (user_id),
    INDEX idx_key_hash (key_hash),
    INDEX idx_is_active (is_active),
    INDEX idx_expires_at (expires_at)
);
```

---

## Rate Limiting Details

### Thresholds

| Endpoint Type | Limit | Window |
|---|---|---|
| Standard API | 100 req/min | 60 sec |
| Webhooks | 1000 req/min | 60 sec |
| Login | 5 failures | 60 sec (ban for 15 min) |

### Implementation

- **Storage**: Redis (fast, no DB overhead)
- **Key format**: `ratelimit:standard:{ip_address}:{window}`
- **Fallback**: Fail open on Redis error (log and allow)
- **IP extraction**: X-Forwarded-For header (for Cloudflare/LB)

### Response Headers

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 42
X-RateLimit-Reset: 1234567890
X-RateLimit-RetryAfter: 30
```

---

## Audit Logging Details

### Event Types

```python
class AuditEventType:
    # Authentication
    LOGIN_SUCCESS, LOGIN_FAILURE, LOGOUT, SESSION_CREATED, 
    PASSWORD_CHANGED, PASSWORD_RESET, MFA_ENABLED, MFA_DISABLED,
    
    # API Access
    API_CALL, API_RATE_LIMIT, API_ERROR, WEBHOOK_RECEIVED,
    
    # Data Access
    DATA_READ, DATA_CREATED, DATA_UPDATED, DATA_DELETED,
    
    # Financial
    PAYMENT_INITIATED, PAYMENT_COMPLETED, PAYMENT_FAILED,
    
    # Admin
    SETTINGS_CHANGED, API_KEY_CREATED, API_KEY_ROTATED,
    ADMIN_ACTION, PERMISSION_CHANGED,
    
    # Security
    SUSPICIOUS_ACTIVITY, LOCATION_CHANGE, DEVICE_ADDED,
    ENCRYPTION_KEY_ROTATED
```

### Retention Policy

- **Default**: 90 days
- **Automatic cleanup**: Daily (Celery task)
- **Configurable**: `AUDIT_LOG_RETENTION_DAYS`

### Query Examples

```python
# All logins in last 7 days
events = await audit_logger.get_events(
    db,
    seller_id="seller_123",
    event_type="login_success",
    start_date=datetime.now() - timedelta(days=7)
)

# All data access for specific user
events = await audit_logger.get_events(
    db,
    seller_id="seller_123",
    event_type="data_read",
    user_id="user_123"
)

# All suspicious activity (risk score > 50)
high_risk = [e for e in events if e.risk_score and e.risk_score > 50]
```

---

## 2FA (TOTP) Details

### Setup Flow

1. **Initiate Setup**
   ```
   POST /api/v1/auth/2fa/setup
   ↓
   Returns: secret, QR code URL, 10 backup codes
   ```

2. **User scans QR code** with authenticator app (Google Authenticator, Authy, etc)

3. **Verify Setup**
   ```
   POST /api/v1/auth/2fa/verify
   Body: { "code": "123456" }
   ↓
   2FA enabled (stored in DB)
   ```

### Login Flow with 2FA

```
POST /api/v1/auth/login
Body: { "email": "user@example.com", "password": "..." }
↓
1. Validate email/password
2. Check if 2FA enabled
3. Return: temp_token (5 min expiry)
4. Frontend shows 2FA input

POST /api/v1/auth/2fa/verify-login
Body: { "code": "123456", "temp_token": "..." }
↓
1. Validate temp token
2. Verify TOTP code
3. Return: full access token
```

### Backup Codes

- **10 codes per user** (one-time use each)
- Shown once during setup (user must save)
- Hashed before storage (SHA256)
- Used if authenticator app lost
- Can't be reused (tracked in `backup_codes_used`)

---

## API Key Management Details

### Key Generation

```
sk_live_{32 hex characters}
├─ Prefix (8 chars)  → displayed in UI
├─ Random portion (32 chars) → never shown again
└─ Hash → stored in DB for verification
```

### Lifecycle

1. **Created**: `created_at`, `created_by`
2. **Active**: Verified on each API call
3. **Used**: `last_used_at`, `last_used_ip` tracked
4. **Rotated**: Old key deactivated, new key created
5. **Revoked**: Immediately deactivated, reason logged
6. **Expired**: Auto-deactivated after 30 days (configurable)

### Scopes

```python
scopes = [
    "orders:read",      # GET /orders
    "orders:write",     # POST/PUT /orders
    "payments:read",    # GET /payments
    "payments:write",   # POST /payments
    "*"                 # Full access (default)
]
```

### Rate Limiting per Key

```python
api_key.rate_limit_per_min = 60  # 60 requests/minute

# Checked per API key in addition to global rate limits
```

---

## Data Isolation (RLS) Details

### Multi-Tenant Model

```
User → Seller Account
   ↓
   ├─ Orders (seller_id filtered)
   ├─ Payments (seller_id filtered)
   ├─ Settings (seller_id filtered)
   └─ API Keys (seller_id filtered)
```

### Query Filter Pattern

**All queries MUST filter by seller_id**:

```python
# ❌ UNSAFE - could leak data
orders = db.query(Order).all()

# ✅ SAFE - filtered by seller_id
orders = db.query(Order).filter(Order.seller_id == user_seller_id).all()

# Or use helper function
orders = DataIsolationService.enforce_seller_id(
    db.query(Order),
    Order,
    user_seller_id
).all()
```

### Violation Handling

```python
# Attempting to access data from different seller → HTTPException(403)
try:
    DataIsolationService.check_seller_id(order, "different_seller_id")
except DataIsolationError:
    # Logged as CRITICAL security event
    # IP may be blocklisted
    # User may be banned
```

---

## Encryption Details

### Fernet Symmetric Encryption

```python
from app.core.encryption import encrypt_value, decrypt_value

# API keys (in database)
encrypted_key = encrypt_value("sk_live_abc123...")
decrypted_key = decrypt_value(encrypted_key)

# Uses:
# - Algorithm: AES-128 in CBC mode
# - HMAC: SHA256 for authentication
# - KDF: PBKDF2 with 480,000 iterations
```

### Environment Setup

```bash
# Generate key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Store in environment
export FERNET_SECRET="<key from above>"
```

### What's Encrypted

- API key values (full key)
- Webhook secrets
- Third-party credentials
- Payment method details (optional)
- Sensitive user PII

### Never Encrypted (indexed/searchable)

- User IDs
- Email addresses (for login)
- Order IDs
- Audit event types

---

## Monitoring & Observability

### Structured Logging

```python
logger.warning("Rate limit exceeded", extra={
    "user_id": "user_123",
    "ip": "192.168.1.1",
    "endpoint": "POST /api/v1/orders",
    "limit": 100,
    "current": 101,
})

logger.critical("Data isolation violation", extra={
    "severity": "critical",
    "user_id": "user_123",
    "attempted_seller_id": "seller_456",
    "resource": "orders/order_123",
})
```

### Metrics (Prometheus)

```
SELLIA_LOGINS_TOTAL{status="success"}
SELLIA_LOGINS_TOTAL{status="failure"}
SELLIA_FAILED_LOGINS_TOTAL{reason="invalid_password|too_many_attempts"}
SELLIA_RATE_LIMIT_HITS_TOTAL{endpoint_type="standard|webhook|login"}
SELLIA_2FA_ENABLED_TOTAL
SELLIA_API_KEYS_GENERATED_TOTAL
SELLIA_AUDIT_EVENTS_TOTAL{event_type="..."}
```

### Dashboards

1. **Authentication Dashboard**
   - Login success/failure rates
   - Failed attempts by IP
   - 2FA adoption rate

2. **Rate Limiting Dashboard**
   - Requests per minute by endpoint
   - Ban events
   - Blocked IPs

3. **API Key Dashboard**
   - Keys by age
   - Expiring keys (30-day forecast)
   - Rotations per user

4. **Audit Log Dashboard**
   - Events by type
   - Risk scores
   - Data access patterns

5. **Data Isolation Dashboard**
   - Isolation violations (CRITICAL)
   - Cross-tenant access attempts (BLOCKED)

---

## Testing

### Run All Tests

```bash
cd backend
pytest tests/test_security.py -v --cov=app.core.security
```

### Test Coverage

- Rate limiter (allow/block)
- Brute force protection
- Audit logging (all event types)
- TOTP setup/verify
- API key generation/verification/rotation
- Data isolation checks

---

## Production Deployment Checklist

- [ ] Generate new `SECRET_KEY` (32+ chars, random)
- [ ] Generate `FERNET_SECRET` key
- [ ] Set `ENVIRONMENT=production`
- [ ] Configure `FRONTEND_URL` (CORS)
- [ ] Enable `CSRF_ENABLED=true`
- [ ] Set strong `METRICS_PASSWORD`
- [ ] Configure Cloudflare DDoS rules
- [ ] Enable PostgreSQL SSL (`DB_SSL_MODE=require`)
- [ ] Set up database backups (daily)
- [ ] Run Alembic migrations (`alembic upgrade head`)
- [ ] Create Celery task for audit log cleanup
- [ ] Set up email notifications for security events
- [ ] Configure log shipping (ELK, DataDog, etc)
- [ ] Test rate limiting (curl with many requests)
- [ ] Test 2FA flow end-to-end
- [ ] Test API key rotation
- [ ] Test data isolation (verify cross-tenant blocks)
- [ ] Enable monitoring/alerts
- [ ] Review audit logs for baseline patterns
- [ ] Document incident response procedures

---

## Support & Documentation

- **Integration Guide**: See `SECURITY_INTEGRATION.md`
- **Code Comments**: Each module has inline docstrings
- **Tests**: See `tests/test_security.py` for usage examples
- **OWASP**: https://owasp.org/www-project-cheat-sheets/
