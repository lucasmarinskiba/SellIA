"""Idempotency Key Middleware.

Prevents duplicate processing of critical operations by caching responses
per Idempotency-Key header.
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from datetime import datetime, timezone
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.domains.security.models import IdempotencyKey
from app.core.logger import get_logger

logger = get_logger(__name__)

# Endpoints where idempotency is enforced
IDEMPOTENT_PATHS = (
    "/api/v1/orders",
    "/api/v1/subscriptions/webhook",
    "/api/v1/businesses",
)


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """Caches responses for POST/PUT/PATCH requests with Idempotency-Key header."""

    async def dispatch(self, request: Request, call_next):
        if request.method not in ("POST", "PUT", "PATCH"):
            return await call_next(request)

        path = request.url.path
        if not any(path.startswith(p) for p in IDEMPOTENT_PATHS):
            return await call_next(request)

        idempotency_key = request.headers.get("Idempotency-Key")
        if not idempotency_key:
            return await call_next(request)

        resource = f"{request.method}:{path}"

        async with AsyncSessionLocal() as db:
            # Check for existing key
            result = await db.execute(
                select(IdempotencyKey).where(
                    IdempotencyKey.key == idempotency_key,
                    IdempotencyKey.resource == resource,
                )
            )
            existing = result.scalar_one_or_none()

            if existing and existing.response_body:
                logger.info(f"Idempotency replay: {idempotency_key}")
                return JSONResponse(
                    status_code=200,
                    content=existing.response_body,
                    headers={"Idempotency-Replay": "true"},
                )

            # Process request
            response = await call_next(request)

            # Cache successful responses (2xx)
            if 200 <= response.status_code < 300:
                try:
                    # Read response body
                    body = b""
                    async for chunk in response.body_iterator:
                        body += chunk

                    # Reconstruct response for downstream
                    import json
                    content = json.loads(body) if body else None

                    key_entry = IdempotencyKey(
                        key=idempotency_key,
                        resource=resource,
                        response_body=json.dumps(content) if content else None,
                    )
                    db.add(key_entry)
                    await db.commit()

                    # Return reconstructed response
                    return JSONResponse(
                        status_code=response.status_code,
                        content=content,
                        headers=dict(response.headers),
                    )
                except Exception as e:
                    logger.warning(f"Failed to cache idempotency response: {e}")
                    # Fall through to return original response

            return response
