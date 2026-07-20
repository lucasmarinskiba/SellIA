from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class CacheControlMiddleware(BaseHTTPMiddleware):
    """
    Inyecta headers Cache-Control agresivos en endpoints que manejan
    datos sensibles (PII, auth, conversaciones, finanzas, etc.).
    """

    SENSITIVE_PREFIXES = (
        "/api/v1/auth",
        "/api/v1/users",
        "/api/v1/businesses",
        "/api/v1/conversations",
        "/api/v1/orders",
        "/api/v1/finance",
        "/api/v1/security",
        "/api/v1/crm",
        "/api/v1/shipments",
        "/api/v1/services",
        "/api/v1/assistant",
        "/api/v1/agents",
        "/api/v1/subscriptions",
        "/api/v1/channels",
    )

    # Rutas públicas que SÍ pueden cachearse (assets, health, tracking pixel)
    ALLOW_CACHE_PREFIXES = (
        "/health",
        "/metrics",
        "/api/v1/tracking",
    )

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        path = request.url.path

        # No sobreescribir si ya tiene Cache-Control explícito
        if "cache-control" in response.headers:
            return response

        # Permitir cacheo en rutas públicas explícitas
        if any(path.startswith(p) for p in self.ALLOW_CACHE_PREFIXES):
            return response

        # Aplicar no-cache en rutas sensibles
        if any(path.startswith(p) for p in self.SENSITIVE_PREFIXES):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

        return response
