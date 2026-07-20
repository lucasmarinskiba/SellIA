"""CSRF protection middleware for cookie-based auth.

Sets a double-submit cookie (csrf_token) and expects the same value
in the X-CSRF-Token header for state-changing requests.
"""

import secrets

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}


class CSRFMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, cookie_name: str = "csrf_token", header_name: str = "X-CSRF-Token"):
        super().__init__(app)
        self.cookie_name = cookie_name
        self.header_name = header_name

    async def dispatch(self, request: Request, call_next):
        cookie_token = request.cookies.get(self.cookie_name)

        # If no CSRF cookie exists, set one (first visit or after clear)
        if not cookie_token:
            cookie_token = secrets.token_urlsafe(32)

        # Validate on state-changing requests
        if request.method not in SAFE_METHODS:
            header_token = request.headers.get(self.header_name, "")
            if not header_token or not secrets.compare_digest(header_token, cookie_token):
                from fastapi.responses import JSONResponse
                return JSONResponse(
                    status_code=403,
                    content={"detail": "CSRF token missing or invalid"},
                )

        response = await call_next(request)

        # Always refresh the CSRF cookie
        response.set_cookie(
            key=self.cookie_name,
            value=cookie_token,
            httponly=False,  # Must be readable by JS for double-submit
            secure=False,    # Set True in production via proxy
            samesite="strict",
            path="/",
            max_age=86400 * 7,
        )
        return response
