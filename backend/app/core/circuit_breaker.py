"""Circuit Breaker pattern for external API calls.

Prevents cascading failures when external services are down.
"""

import time
import asyncio
from enum import Enum
from typing import Callable, Optional
from functools import wraps
from app.core.logger import get_logger

logger = get_logger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing fast
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """Simple circuit breaker for async functions.

    Args:
        failure_threshold: Number of failures before opening circuit
        recovery_timeout: Seconds to wait before trying half-open
        half_open_max_calls: Number of successful calls to close circuit
        expected_exception: Exception type that counts as failure
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        half_open_max_calls: int = 3,
        expected_exception: type = Exception,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        self.expected_exception = expected_exception

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self._lock = asyncio.Lock()

    async def call(self, func: Callable, *args, **kwargs):
        async with self._lock:
            if self.state == CircuitState.OPEN:
                if time.time() - self.last_failure_time >= self.recovery_timeout:
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                    logger.info(f"Circuit breaker entering HALF_OPEN for {func.__qualname__}")
                else:
                    raise CircuitBreakerOpen(f"Circuit is OPEN for {func.__qualname__}")

        try:
            result = await func(*args, **kwargs)
        except self.expected_exception as e:
            await self._on_failure()
            raise

        await self._on_success()
        return result

    async def _on_success(self):
        async with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.half_open_max_calls:
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    logger.info("Circuit breaker CLOSED (recovered)")
            else:
                self.failure_count = 0

    async def _on_failure(self):
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.OPEN
                logger.warning("Circuit breaker OPEN (half-open test failed)")
            elif self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                logger.warning(f"Circuit breaker OPEN after {self.failure_count} failures")

    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await self.call(func, *args, **kwargs)
        return wrapper


class CircuitBreakerOpen(Exception):
    """Raised when the circuit breaker is open."""
    pass


# Pre-configured breakers for common external services
stripe_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=30)
mercadopago_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=30)
openai_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=15)
whatsapp_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)
