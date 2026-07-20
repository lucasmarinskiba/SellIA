from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Inyecta headers de seguridad HTTP en todas las respuestas."""

    def __init__(self, app: ASGIApp, csp_report_uri: str | None = None):
        super().__init__(app)
        self.csp_report_uri = csp_report_uri

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Anti-clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Anti-MIME-sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # HSTS (solo en producción con HTTPS real; el proxy/Nginx debe forzarlo)
        response.headers["Strict-Transport-Security"] = (
            "max-age=63072000; includeSubDomains; preload"
        )

        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions policy (evita que sitios embedidos usen APIs sensibles)
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), payment=(), usb=(), "
            "magnetometer=(), gyroscope=(), accelerometer=()"
        )

        # Content Security Policy (coordinar con frontend)
        csp = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'; "
            "upgrade-insecure-requests;"
        )
        if self.csp_report_uri:
            csp += f" report-uri {self.csp_report_uri};"
        response.headers["Content-Security-Policy"] = csp

        # Cross-Origin policies (defensa contra Spectre y data leakage)
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"

        # OCSP Stapling / Certificate Transparency helpers
        response.headers["Expect-CT"] = "max-age=86400, enforce"

        # Remove server identification
        try:
            del response.headers["Server"]
        except KeyError:
            pass

        return response
