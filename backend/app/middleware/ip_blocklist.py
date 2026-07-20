"""Auto IP Blocklist Middleware.

Bloquea requests de IPs que están en la tabla blocked_ips.
Se ejecuta después de ThreatIntelMiddleware para poder bloquear
IPs detectadas como amenazas.
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from datetime import datetime, timezone
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.domains.security.models import BlockedIP
from app.core.logger import get_logger

logger = get_logger(__name__)


class IPBlocklistMiddleware(BaseHTTPMiddleware):
    """Rechaza requests de IPs bloqueadas."""

    async def dispatch(self, request: Request, call_next):
        client_ip = getattr(request.state, "client_ip", None) or request.client.host

        # Skip health checks
        if request.url.path in ("/health", "/nginx-health", "/metrics"):
            return await call_next(request)

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(BlockedIP).where(
                    BlockedIP.ip_address == client_ip,
                )
            )
            blocked = result.scalar_one_or_none()

            if blocked:
                # Verificar si el bloqueo tiene fecha de expiración
                if blocked.blocked_until and blocked.blocked_until < datetime.now(timezone.utc):
                    # Desbloquear automáticamente
                    await db.delete(blocked)
                    await db.commit()
                    logger.info(f"Auto-unblocked IP {client_ip}")
                else:
                    logger.warning(f"Blocked request from {client_ip}: {blocked.reason}")
                    return JSONResponse(
                        status_code=403,
                        content={"detail": "IP bloqueada por seguridad"},
                    )

        return await call_next(request)
