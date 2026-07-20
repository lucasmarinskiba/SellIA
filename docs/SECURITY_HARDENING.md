# SellIA Security Hardening Guide

Comprehensive security configurations and best practices for production deployment.

## 1. HTTPS & TLS Configuration

### SSL/TLS Certificate Management
```bash
# Generate certificates with Let's Encrypt
certbot certonly --standalone \
  -d api.selldia.app \
  -d selldia.app \
  -d www.selldia.app

# Auto-renewal
sudo systemctl enable certbot-renew.timer
sudo systemctl start certbot-renew.timer
```

### Nginx SSL Configuration (Already in nginx.conf)
```nginx
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers HIGH:!aNULL:!MD5;
ssl_prefer_server_ciphers on;
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;
ssl_stapling on;
ssl_stapling_verify on;
```

## 2. API Security

### Rate Limiting
```python
# backend/app/core/security.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# Apply to routes
@app.get("/api/auth/login")
@limiter.limit("5/minute")
async def login(request: Request, credentials: LoginRequest):
    pass
```

### CORS Configuration
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "https://selldia.app").split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
    max_age=3600,
)
```

### API Key Validation
```python
# backend/app/core/security.py
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthCredentials

security = HTTPBearer()

async def verify_api_key(credentials: HTTPAuthCredentials = Depends(security)):
    token = credentials.credentials
    if not validate_token(token):
        raise HTTPException(status_code=401, detail="Invalid API key")
    return token
```

### JWT Token Security
```python
# backend/app/core/security.py
from datetime import datetime, timedelta
import jwt

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=24)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
```

## 3. Database Security

### Connection Encryption
```python
# backend/app/core/database.py
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(
    DATABASE_URL,
    connect_args={"sslmode": "require"},  # Force SSL
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,  # Verify connections before use
)
```

### SQL Injection Prevention
```python
# Use ORM/parameterized queries (SQLAlchemy)
from sqlalchemy import select

# Good (parameterized)
query = select(User).where(User.email == email)

# Bad (vulnerable)
query = f"SELECT * FROM users WHERE email = '{email}'"
```

### Secrets Management
```python
# Use environment variables, never hardcode secrets
from dotenv import load_dotenv
import os

load_dotenv(".env.production")

DATABASE_PASSWORD = os.getenv("DB_PASSWORD")
STRIPE_KEY = os.getenv("STRIPE_API_KEY")
JWT_SECRET = os.getenv("SECRET_KEY")

# For additional security, use AWS Secrets Manager or HashiCorp Vault
```

## 4. Authentication & Authorization

### Password Security
```python
# backend/app/core/security.py
from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,  # CPU cost factor
)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed: str) -> bool:
    return pwd_context.verify(plain_password, hashed)
```

### Two-Factor Authentication (2FA)
```python
# backend/app/core/security.py
import pyotp
import qrcode

def generate_2fa_secret(user_id: str):
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    
    # Generate QR code
    qr = qrcode.QRCode()
    qr.add_data(totp.provisioning_uri(name=user_id, issuer_name='SellIA'))
    
    return secret, qr.make_image()

def verify_2fa_token(secret: str, token: str) -> bool:
    totp = pyotp.TOTP(secret)
    return totp.verify(token)
```

### Role-Based Access Control (RBAC)
```python
# backend/app/core/security.py
from enum import Enum

class Role(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"

async def verify_role(required_role: Role, token: str = Depends(verify_token)):
    user_role = get_user_role(token)
    if user_role not in get_required_roles(required_role):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return user_role
```

## 5. Data Protection

### Encryption at Rest
```python
# backend/app/core/security.py
from cryptography.fernet import Fernet

cipher_suite = Fernet(os.getenv("ENCRYPTION_KEY").encode())

def encrypt_sensitive_data(data: str) -> str:
    return cipher_suite.encrypt(data.encode()).decode()

def decrypt_sensitive_data(encrypted_data: str) -> str:
    return cipher_suite.decrypt(encrypted_data.encode()).decode()
```

### PII Masking
```python
# backend/app/utils/masking.py
import re

def mask_email(email: str) -> str:
    local, domain = email.split("@")
    return f"{local[:2]}***@{domain}"

def mask_phone(phone: str) -> str:
    return f"***-***-{phone[-4:]}"

def mask_credit_card(card: str) -> str:
    return f"****-****-****-{card[-4:]}"
```

### Data Retention Policy
```python
# backend/app/tasks/cleanup.py
from celery import shared_task
from datetime import datetime, timedelta

@shared_task
def cleanup_old_data():
    """Delete data older than 90 days"""
    cutoff_date = datetime.utcnow() - timedelta(days=90)
    
    # Delete old logs
    AuditLog.query.filter(AuditLog.created_at < cutoff_date).delete()
    
    # Delete old sessions
    Session.query.filter(Session.created_at < cutoff_date).delete()
    
    db.session.commit()
```

## 6. Logging & Auditing

### Structured Logging
```python
# backend/app/core/logging.py
import structlog
import json

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
)

logger = structlog.get_logger()

# Log security events
logger.info("user_login", user_id=user.id, ip_address=request.client.host)
logger.warning("failed_auth_attempt", email=email, ip_address=request.client.host)
logger.error("suspicious_activity", event="multiple_failed_attempts", user_id=user.id)
```

### Audit Trail
```python
# backend/app/models/audit.py
from sqlalchemy import Column, String, DateTime, JSON
from datetime import datetime

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(String, primary_key=True)
    user_id = Column(String)
    action = Column(String)  # created, updated, deleted
    entity_type = Column(String)  # User, SalesCycle, etc.
    entity_id = Column(String)
    changes = Column(JSON)  # Before/after values
    ip_address = Column(String)
    user_agent = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
```

## 7. DDoS Protection

### Cloudflare Configuration
```bash
# Enable in Cloudflare dashboard:
1. Security → DDoS Protection
2. Set DDoS Sensitivity: High
3. Enable Advanced DDoS Protection (Enterprise)
4. Rate Limiting Rules (custom)
5. Bot Management
6. Web Application Firewall (WAF)
```

### Nginx Rate Limiting (Already configured)
```nginx
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=60r/m;
limit_req zone=api_limit burst=100 nodelay;
```

## 8. Infrastructure Security

### Firewall Rules
```bash
# Allow only necessary ports
# 22 (SSH - restricted to VPN)
# 80 (HTTP - redirect to HTTPS)
# 443 (HTTPS)
# 5432 (PostgreSQL - internal only)
# 6379 (Redis - internal only)
```

### Network Isolation
```yaml
# docker-compose.yml
networks:
  sellianet:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16

services:
  postgres:
    networks:
      - sellianet
  
  redis:
    networks:
      - sellianet
  
  backend:
    networks:
      - sellianet
  
  nginx:
    networks:
      - sellianet
```

## 9. Third-Party Security

### Payment Processing (PCI-DSS)
```python
# Never handle credit card data directly
# Use Stripe/MercadoPago tokenization

# Good: Tokenized payments
@app.post("/api/payments")
async def create_payment(payment: PaymentRequest):
    # payment.token is from Stripe.js, not the card
    charge = stripe.Charge.create(
        amount=payment.amount,
        currency="usd",
        source=payment.token,
    )
```

### Webhook Verification
```python
# backend/app/api/webhooks.py
import hmac
import hashlib

def verify_stripe_webhook(payload: bytes, signature: str) -> bool:
    computed_sig = hmac.new(
        STRIPE_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(computed_sig, signature)

@app.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    signature = request.headers.get("stripe-signature")
    
    if not verify_stripe_webhook(payload, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Process event
```

## 10. Compliance & Legal

### GDPR Compliance
```python
# backend/app/api/users.py

@app.delete("/api/users/{user_id}")
async def delete_user_data(user_id: str, current_user: User = Depends(verify_token)):
    # Right to be forgotten
    user = User.query.get(user_id)
    
    # Anonymize sensitive data
    user.email = f"deleted_{uuid4()}@example.com"
    user.phone = None
    user.name = "Deleted User"
    
    # Delete personal data
    db.session.delete_all_related_data(user_id)
    db.session.commit()
    
    log_gdpr_deletion(user_id)
```

### CCPA Compliance
```python
# backend/app/api/privacy.py

@app.get("/api/privacy/data-export")
async def export_user_data(current_user: User = Depends(verify_token)):
    # Provide all user data in machine-readable format
    data = {
        "personal_info": current_user.to_dict(),
        "activity_logs": AuditLog.query.filter_by(user_id=current_user.id).all(),
        "sales_data": SalesCycle.query.filter_by(user_id=current_user.id).all(),
    }
    return data
```

## 11. Security Testing

### Regular Penetration Testing
```bash
# Run security audit tools
# - OWASP ZAP
# - Burp Suite
# - Nessus
# - SonarQube

# Schedule quarterly penetration tests with third party
```

### Dependency Vulnerability Scanning
```bash
# Check for vulnerabilities
pip install safety
safety check

# Update requirements regularly
pip list --outdated
pip install --upgrade -r requirements.txt
```

### Secrets Scanning
```bash
# Scan for hardcoded secrets
pip install detect-secrets
detect-secrets scan

# Or use GitHub's built-in secret scanning
```

## 12. Incident Response

### Security Incident Playbook
```markdown
1. Detection: Alert from monitoring/security tools
2. Containment: Isolate affected systems
3. Investigation: Analyze logs and evidence
4. Remediation: Fix the vulnerability
5. Recovery: Restore services
6. Post-incident: Review and improve
```

### Emergency Procedures
```bash
# Rotate all secrets
./scripts/rotate_secrets.sh

# Kill all sessions
DELETE FROM sessions;

# Revoke API keys
UPDATE api_keys SET active = false;

# Backup and archive logs
tar -czf /backups/incident_$(date +%Y%m%d_%H%M%S).tar.gz /var/log/
```

## Security Checklist

- [ ] SSL/TLS configured (TLSv1.2+)
- [ ] HTTPS enforced (HSTS header)
- [ ] Rate limiting enabled
- [ ] CORS properly configured
- [ ] JWT secrets rotated
- [ ] Database SSL enabled
- [ ] 2FA available for users
- [ ] Password hashing (bcrypt, 12+ rounds)
- [ ] Audit logging enabled
- [ ] Secrets in environment variables only
- [ ] PII encryption at rest
- [ ] Data retention policies implemented
- [ ] Firewall rules configured
- [ ] DDoS protection enabled
- [ ] Backup and disaster recovery tested
- [ ] Security patches applied
- [ ] Vulnerability scanning automated
- [ ] Incident response plan documented
- [ ] Privacy policy compliant
- [ ] Regular security audits scheduled
