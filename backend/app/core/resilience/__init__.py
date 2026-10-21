"""Resilience module — Retry engines, circuit breakers, failover logic."""
import asyncio
import logging
import re as _re
from collections.abc import Callable
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class ServiceHealthTracker:
    def __init__(self):
        self.services: dict[str, Any] = {}

    def get_breaker(self, service_name: str):
        if service_name not in self.services:
            self.services[service_name] = {"failures": 0, "state": CircuitState.CLOSED}
        return self.services[service_name]

    def is_service_available(self, service_name: str) -> bool:
        return True

    def record_success(self, service_name: str):
        pass

    def record_failure(self, service_name: str):
        pass

    def status(self) -> dict[str, str]:
        return {}


health_tracker = ServiceHealthTracker()


async def retry_with_exponential_backoff(func: Callable, args: tuple = (), kwargs: dict = None, max_retries: int = 3, initial_delay: float = 1.0, is_idempotent: bool = True) -> Any:
    if kwargs is None:
        kwargs = {}
    if not is_idempotent:
        return await func(*args, **kwargs)
    delay = initial_delay
    last_exception = None
    for attempt in range(max_retries):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.exception("retry_with_exponential_backoff: error inesperado")
            last_exception = e
            if attempt < max_retries - 1:
                await asyncio.sleep(delay)
                delay *= 2
    raise last_exception

# InputValidator lives in app/core/input_validation.py (moved out of the old
# app/core/resilience.py file, which collided with this package's name and
# was silently shadowed by it) — re-exported here so existing callers of
# `from app.core.resilience import InputValidator` keep working.
from app.core.input_validation import InputValidator

from .retry_engine import (
    CircuitBreaker,
    CircuitBreakerState,
    RetryAttempt,
    RetryConfig,
    RetryEngine,
    RetryHistory,
    RetryPolicy,
    retry,
    retry_engine,
)

__all__ = [
    "CircuitBreaker",
    "CircuitBreakerState",
    "CircuitState",
    "InputValidator",
    "RetryAttempt",
    "RetryConfig",
    "RetryEngine",
    "RetryHistory",
    "RetryPolicy",
    "ServiceHealthTracker",
    "health_tracker",
    "retry",
    "retry_engine",
    "retry_with_exponential_backoff",
]
