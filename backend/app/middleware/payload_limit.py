from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware


class PayloadLimitMiddleware(BaseHTTPMiddleware):
    """
    Rechaza requests cuyo body exceda el tamaño máximo permitido.
    Protege contra ataques de denegación de servicio por payloads enormes.

    NOTA: Este middleware verifica Content-Length. Para protección completa
    contra chunked uploads maliciosos, configurar también client_max_body_size
    en Nginx o el ASGI server (Uvicorn).
    """

    def __init__(self, app, max_size_bytes: int = 10 * 1024 * 1024):
        super().__init__(app)
        self.max_size_bytes = max_size_bytes

    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
            except ValueError:
                size = 0
            if size > self.max_size_bytes:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"Payload exceeds maximum size of {self.max_size_bytes} bytes",
                )
        return await call_next(request)
