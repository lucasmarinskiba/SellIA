"""Data Access Audit Log Middleware.

Logs access to sensitive data endpoints for compliance and forensics.
"""

import uuid
from datetime import datetime, timezone
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logger import get_logger

logger = get_logger(__name__)

# Endpoints that access sensitive data
SENSITIVE_PATHS = [
    "/conversations",
    "/orders",
    "/finance",
    "/objectives",
    "/retention",
    "/bi",
    "/users",
]


class DataAccessAuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        path = request.url.path
        if not any(p in path for p in SENSITIVE_PATHS):
            return response

        user_id = None
        business_id = None
        try:
            if hasattr(request.state, "user") and request.state.user:
                user_id = str(request.state.user.id)
            # Try to extract business_id from path
            parts = path.strip("/").split("/")
            for i, part in enumerate(parts):
                if part == "businesses" and i + 1 < len(parts):
                    try:
                        uuid.UUID(parts[i + 1])
                        business_id = parts[i + 1]
                    except ValueError:
                        pass
        except Exception:
            pass

        # Async fire-and-forget to DB (non-blocking)
        try:
            from app.core.database import AsyncSessionLocal
            from app.domains.security.models import DataAccessLog

            async def _log():
                async with AsyncSessionLocal() as db:
                    log = DataAccessLog(
                        user_id=uuid.UUID(user_id) if user_id else None,
                        business_id=uuid.UUID(business_id) if business_id else None,
                        action=request.method.lower(),
                        table_name=path.split("/")[-1] if path else "unknown",
                        ip_address=request.client.host if request.client else None,
                        user_agent=request.headers.get("user-agent"),
                        request_path=path,
                    )
                    db.add(log)
                    await db.commit()

            import asyncio
            asyncio.create_task(_log())
        except Exception:
            pass

        return response
