"""Centralized exception handling utilities."""

import traceback
from typing import Optional
from fastapi import HTTPException, status
from app.core.logger import get_logger

logger = get_logger(__name__)


class AppException(Exception):
    """Base application exception carrying an HTTP status code + client-safe
    message. Register a handler for it (see app.core.multi_tenant
    .app_setup_example for the FastAPI wiring) to turn any `raise
    AppException("msg", status_code=404)` into a proper JSON error response.

    Was referenced across 10 files in app.core.multi_tenant (tenant CRUD,
    billing, API keys, audit logging, isolation) but never defined —
    the entire module was unimportable. See that package's models.py
    docstring for the table-collision issue also found there.
    """

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        error_code: Optional[str] = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or "APP_ERROR"
        super().__init__(message)


def sanitize_internal_error(exc: Exception) -> HTTPException:
    """Log full exception internally, return generic error to client."""
    logger.exception("Internal server error")
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Internal server error",
    )


def log_and_return_error(exc: Exception, operation: str = "operation") -> dict:
    """For webhook/background tasks that return JSON instead of raising."""
    logger.exception(f"Error during {operation}")
    return {"status": "error", "detail": "Internal server error"}
