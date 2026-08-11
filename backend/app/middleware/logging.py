"""Structured logging with correlation IDs for traceability."""

import logging
import json
import sys
from pythonjsonlogger import jsonlogger
from contextvars import ContextVar
from typing import Any, Dict, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request


# Context variable for correlation ID (thread-safe)
correlation_id_context: ContextVar[str] = ContextVar(
    "correlation_id",
    default=""
)

user_id_context: ContextVar[str] = ContextVar(
    "user_id",
    default=""
)

request_id_context: ContextVar[str] = ContextVar(
    "request_id",
    default=""
)


class CorrelationIdFilter(logging.Filter):
    """
    Add correlation ID to every log record.

    Enables filtering logs by correlation_id in CloudWatch/ELK.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = correlation_id_context.get()
        record.user_id = user_id_context.get()
        record.request_id = request_id_context.get()
        return True


class JSONFormatter(jsonlogger.JsonFormatter):
    """
    JSON log formatter with custom fields.

    Output: single JSON line per log, easily parsed by log aggregation.
    """

    def add_fields(
        self,
        log_record: Dict[str, Any],
        record: logging.LogRecord,
        message_dict: Dict[str, Any],
    ) -> None:
        super().add_fields(log_record, record, message_dict)

        # Standard fields
        log_record["timestamp"] = self.formatTime(record)
        log_record["level"] = record.levelname
        log_record["logger"] = record.name
        log_record["module"] = record.module
        log_record["function"] = record.funcName
        log_record["line"] = record.lineno

        # Tracing fields
        log_record["correlation_id"] = getattr(record, "correlation_id", "")
        log_record["user_id"] = getattr(record, "user_id", "")
        log_record["request_id"] = getattr(record, "request_id", "")

        # Error fields
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
            log_record["exception_type"] = record.exc_info[0].__name__

        # Performance fields
        if hasattr(record, "duration_ms"):
            log_record["duration_ms"] = record.duration_ms
        if hasattr(record, "status_code"):
            log_record["status_code"] = record.status_code


def setup_logging(
    level: str = "INFO",
    json_format: bool = True,
) -> logging.Logger:
    """
    Configure structured logging with JSON format.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        json_format: Use JSON format (vs plain text)

    Returns:
        Configured logger
    """

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers
    root_logger.handlers.clear()

    # Create handler
    handler = logging.StreamHandler(sys.stdout)

    # Add correlation ID filter
    handler.addFilter(CorrelationIdFilter())

    if json_format:
        # JSON format
        formatter = JSONFormatter(
            fmt="%(timestamp)s %(level)s %(logger)s %(message)s"
        )
    else:
        # Plain text format with color
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - [%(correlation_id)s] - %(message)s"
        )

    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get logger with context vars attached."""
    return logging.getLogger(name)


class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    Populate context variables from request.

    Enables correlation_id + user_id in all logs without passing params.
    """

    async def dispatch(self, request: Request, call_next):
        # Extract correlation ID from header or generate
        correlation_id = request.headers.get(
            "X-Correlation-ID",
            ""
        )
        correlation_id_context.set(correlation_id)

        # Extract user ID from auth (if available)
        user_id = request.headers.get("X-User-ID", "")
        if not user_id and hasattr(request.state, "user_id"):
            user_id = request.state.user_id
        user_id_context.set(user_id)

        # Generate request ID
        import uuid
        request_id = str(uuid.uuid4())
        request_id_context.set(request_id)

        response = await call_next(request)
        return response


# Example usage:
def example_structured_logging():
    """Show structured logging examples."""

    logger = get_logger(__name__)

    # Simple info
    logger.info("User logged in")
    # Output: {"timestamp": "2026-08-12T14:00:00", "level": "INFO", "logger": "__main__", "message": "User logged in", "correlation_id": "abc-123"}

    # With extra data (becomes extra fields)
    logger.info(
        "Deal approved",
        extra={
            "deal_id": "deal_001",
            "deal_value": 50000,
            "approver_id": "user_123",
            "status": "approved",
            "duration_ms": 245,
        }
    )
    # Output: {..., "message": "Deal approved", "deal_id": "deal_001", "deal_value": 50000, "approver_id": "user_123", "status": "approved", "duration_ms": 245}

    # With warning
    logger.warning(
        "High memory usage detected",
        extra={
            "memory_mb": 4096,
            "threshold_mb": 3072,
            "percent": 87.5,
        }
    )

    # With error + exception
    try:
        1 / 0
    except ZeroDivisionError:
        logger.error(
            "Database calculation failed",
            exc_info=True,
            extra={
                "query": "SELECT AVG(value) FROM deals",
                "db_host": "db.internal",
            }
        )
    # Output: {..., "exception": "Traceback...", "exception_type": "ZeroDivisionError"}


# Filtering examples (in log aggregation like CloudWatch):
#
# Find all errors for a specific deal:
#   correlation_id=abc-123 AND level=ERROR
#
# Find all slow requests:
#   duration_ms > 1000
#
# Find all user actions:
#   user_id=user_123 AND level=INFO
#
# Find all database errors:
#   logger=database AND level=ERROR
#
# Performance analysis:
#   fields @duration_ms | stats avg(@duration_ms), max(@duration_ms), pct(@duration_ms, 99)
