"""
Subscription Audit Middleware

Loguea cada request a features protegidas para evidencia de entrega de servicio.
"""

import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.domains.subscriptions.integrity import log_feature_access
from app.core.logger import get_logger

logger = get_logger(__name__)

# Endpoints que se auditan
AUDITED_PREFIXES = [
    "/api/v1/agents",
    "/api/v1/businesses",
    "/api/v1/catalog",
    "/api/v1/conversations",
    "/api/v1/channels",
    "/api/v1/automations",
    "/api/v1/analytics",
    "/api/v1/crm",
    "/api/v1/orders",
]


class SubscriptionAuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        path = request.url.path

        # Check if path should be audited
        should_audit = any(path.startswith(prefix) for prefix in AUDITED_PREFIXES)

        response = await call_next(request)

        if should_audit:
            try:
                duration_ms = int((time.time() - start_time) * 1000)
                user = getattr(request.state, "current_user", None)

                if user and not getattr(user, "is_superuser", False):
                    feature_name = _extract_feature_name(path)

                    # Log async (fire and forget)
                    from app.core.database import AsyncSessionLocal
                    async with AsyncSessionLocal() as db:
                        await log_feature_access(
                            db=db,
                            user_id=user.id,
                            feature_name=feature_name,
                            endpoint=path,
                            response_status=response.status_code,
                            response_size=int(response.headers.get("content-length", 0)),
                            duration_ms=duration_ms,
                            success=response.status_code < 400,
                        )
            except Exception as e:
                logger.warning(f"Subscription audit log failed: {e}")

        return response


def _extract_feature_name(path: str) -> str:
    """Extrae el nombre de la feature del path."""
    parts = path.split("/")
    if len(parts) >= 4:
        return parts[3]  # /api/v1/{feature}/...
    return "unknown"
