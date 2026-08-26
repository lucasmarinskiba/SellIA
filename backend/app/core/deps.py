import hashlib
import hmac
import os
from typing import Optional

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import decode_access_token
from app.domains.users.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


SIDECAR_SHARED_SECRET = os.environ.get("SIDECAR_SHARED_SECRET", "")


def _verify_sidecar_signature(request: Request) -> bool:
    """Valida que los headers de sidecar vengan firmados con HMAC-SHA256."""
    if not SIDECAR_SHARED_SECRET:
        return False
    signature = request.headers.get("X-Sidecar-Signature", "")
    user_id = request.headers.get("X-User-Id", "")
    authenticated = request.headers.get("X-Authenticated", "")
    expected = hmac.new(
        SIDECAR_SHARED_SECRET.encode(),
        f"{authenticated}:{user_id}".encode(),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(signature, expected)


async def get_token_from_request(request: Request) -> str | None:
    """Obtiene el token desde header Bearer o cookie httpOnly."""
    # 1. Intentar header Authorization
    auth = request.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:]

    # 2. Intentar cookie httpOnly (Fase 6)
    token_cookie = request.cookies.get("access_token")
    if token_cookie:
        return token_cookie

    return None


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = await get_token_from_request(request)
    if token is None:
        raise credentials_exception

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    try:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None or not user.is_active:
            raise credentials_exception
        return user
    except HTTPException:
        raise
    except Exception as e:
        from app.core.logger import get_logger
        get_logger(__name__).exception("User query failed")
        raise credentials_exception


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo",
        )
    return current_user


# Dependency de rate limiting (wrapper para fastapi-limiter)
from fastapi_limiter.depends import RateLimiter

# Re-exportar para uso en routers
RateLimit = RateLimiter


async def get_current_user_ws(token: Optional[str], db: AsyncSession = Depends(get_db)) -> Optional[User]:
    """Validate user from JWT token for WebSocket connections (no HTTP Request)."""
    if not token:
        return None
    payload = decode_access_token(token)
    if payload is None:
        return None
    user_id = payload.get("sub")
    if user_id is None:
        return None
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        return None
    return user
