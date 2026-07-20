"""Centralized exception handling utilities."""

import traceback
from fastapi import HTTPException, status
from app.core.logger import get_logger

logger = get_logger(__name__)


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
