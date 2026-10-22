"""Security package for SellIA.

Modules:
- rate_limiter: Rate limiting and DDoS protection
- audit_logger: Audit logging for compliance
- auth_factors: 2FA and API key management
- data_isolation: Per-user data isolation (RLS)
"""

import re
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.core.config import get_settings as _get_settings

_settings = _get_settings()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


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


def create_access_token(
    data: dict[str, Any], expires_delta: timedelta | None = None
) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=_settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, _settings.SECRET_KEY, algorithm=_settings.ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any] | None:
    try:
        return jwt.decode(token, _settings.SECRET_KEY, algorithms=[_settings.ALGORITHM])
    except JWTError:
        return None


from app.core.security.audit_logger import (
    AuditEventType,
    AuditLog,
    AuditLogger,
    get_audit_logger,
)
from app.core.security.auth_factors import (
    TOTP2FA,
    APIKey,
    APIKeyService,
    Auth2FAService,
    get_api_key_service,
    get_auth_2fa_service,
)
from app.core.security.data_isolation import (
    DataIsolationError,
    DataIsolationService,
    SellerContext,
    get_seller_context,
)
from app.core.security.rate_limiter import (
    RateLimiter,
    get_rate_limiter,
)

__all__ = [
    # 2FA & API Keys
    "TOTP2FA",
    "APIKey",
    "APIKeyService",
    "AuditEventType",
    # Audit Logger
    "AuditLog",
    "AuditLogger",
    "Auth2FAService",
    "DataIsolationError",
    # Data Isolation
    "DataIsolationService",
    # Rate Limiter
    "RateLimiter",
    "SellerContext",
    "create_access_token",
    "decode_access_token",
    "get_api_key_service",
    "get_audit_logger",
    "get_auth_2fa_service",
    "get_password_hash",
    "get_rate_limiter",
    "get_seller_context",
    "validate_password_strength",
    # Auth utils
    "verify_password",
]
