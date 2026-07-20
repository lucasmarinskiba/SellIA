"""Security package for SellIA.

Modules:
- rate_limiter: Rate limiting and DDoS protection
- audit_logger: Audit logging for compliance
- auth_factors: 2FA and API key management
- data_isolation: Per-user data isolation (RLS)
"""

import re
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Any
from jose import jwt, JWTError
from app.core.config import get_settings as _get_settings

_settings = _get_settings()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def validate_password_strength(password: str) -> None:
    if len(password) < 10:
        raise ValueError("La contraseña debe tener al menos 10 caracteres.")
    if not re.search(r"[A-Z]", password):
        raise ValueError("La contraseña debe contener al menos una mayúscula.")
    if not re.search(r"[a-z]", password):
        raise ValueError("La contraseña debe contener al menos una minúscula.")
    if not re.search(r"[0-9]", password):
        raise ValueError("La contraseña debe contener al menos un número.")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>\-_=+\[\]/~`\\]", password):
        raise ValueError("La contraseña debe contener al menos un símbolo.")


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=_settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, _settings.SECRET_KEY, algorithm=_settings.ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any] | None:
    try:
        return jwt.decode(token, _settings.SECRET_KEY, algorithms=[_settings.ALGORITHM])
    except JWTError:
        return None


from app.core.security.rate_limiter import (
    RateLimiter,
    get_rate_limiter,
)
from app.core.security.audit_logger import (
    AuditLog,
    AuditEventType,
    AuditLogger,
    get_audit_logger,
)
from app.core.security.auth_factors import (
    TOTP2FA,
    APIKey,
    Auth2FAService,
    APIKeyService,
    get_auth_2fa_service,
    get_api_key_service,
)
from app.core.security.data_isolation import (
    DataIsolationService,
    DataIsolationError,
    SellerContext,
    get_seller_context,
)

__all__ = [
    # Auth utils
    "verify_password",
    "get_password_hash",
    "validate_password_strength",
    "create_access_token",
    "decode_access_token",
    # Rate Limiter
    "RateLimiter",
    "get_rate_limiter",
    # Audit Logger
    "AuditLog",
    "AuditEventType",
    "AuditLogger",
    "get_audit_logger",
    # 2FA & API Keys
    "TOTP2FA",
    "APIKey",
    "Auth2FAService",
    "APIKeyService",
    "get_auth_2fa_service",
    "get_api_key_service",
    # Data Isolation
    "DataIsolationService",
    "DataIsolationError",
    "SellerContext",
    "get_seller_context",
]
