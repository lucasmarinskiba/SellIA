"""Computer Use — Smart Retry Handler

Reintentos inteligentes con backoff exponencial, jitter, y circuit breaker.
Maneja fallos transitorios de navegador, red, y APIs de LLM.
"""

import asyncio
import random
from typing import Callable, TypeVar, Optional, List
from dataclasses import dataclass
from enum import Enum

from app.core.logger import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject fast
    HALF_OPEN = "half_open"  # Testing if recovered


@dataclass
class RetryConfig:
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    exponential_base: float = 2.0
    jitter: bool = True
    retryable_exceptions: tuple = (Exception,)
    on_retry: Optional[Callable] = None


@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5
    recovery_timeout: float = 30.0
    half_open_max_calls: int = 2


class RetryHandler:
    """Handler de reintentos con circuit breaker."""

    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()

    async def execute(
        self,
        func: Callable[..., T],
        *args,
        **kwargs,
    ) -> T:
        """Ejecuta una función con reintentos."""
        last_exception = None

        for attempt in range(self.config.max_retries + 1):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            except self.config.retryable_exceptions as e:
                last_exception = e
                if attempt < self.config.max_retries:
                    delay = self._calculate_delay(attempt)
                    logger.warning(
                        f"Retry {attempt + 1}/{self.config.max_retries} after {delay:.1f}s: {e}"
                    )
                    if self.config.on_retry:
                        await self.config.on_retry(attempt, e, delay)
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Max retries exceeded: {e}")
                    raise last_exception

        raise last_exception

    def _calculate_delay(self, attempt: int) -> float:
        """Calcula el delay con backoff exponencial y jitter."""
        delay = self.config.base_delay * (self.config.exponential_base ** attempt)
        delay = min(delay, self.config.max_delay)
        if self.config.jitter:
            delay = delay * (0.5 + random.random() * 0.5)
        return delay


class CircuitBreaker:
    """Circuit breaker para proteger contra fallos en cascada."""

    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self._lock = asyncio.Lock()

    async def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Llama a una función con protección de circuit breaker."""
        async with self._lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                    logger.info(f"Circuit {self.name}: HALF_OPEN")
                else:
                    raise CircuitBreakerOpen(f"Circuit {self.name} is OPEN")

        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure()
            raise

    def _should_attempt_reset(self) -> bool:
        import time
        if self.last_failure_time is None:
            return True
        return time.time() - self.last_failure_time >= self.config.recovery_timeout

    async def _on_success(self):
        async with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.half_open_max_calls:
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    logger.info(f"Circuit {self.name}: CLOSED")
            else:
                self.failure_count = max(0, self.failure_count - 1)

    async def _on_failure(self):
        import time
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.OPEN
                logger.warning(f"Circuit {self.name}: OPEN (half-open failed)")
            elif self.failure_count >= self.config.failure_threshold:
                self.state = CircuitState.OPEN
                logger.warning(f"Circuit {self.name}: OPEN ({self.failure_count} failures)")

    def get_state(self) -> dict:
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
        }


class CircuitBreakerOpen(Exception):
    """Excepción cuando el circuit breaker está abierto."""
    pass


# Circuit breakers por servicio
_circuit_breakers: dict = {}


def get_circuit_breaker(name: str) -> CircuitBreaker:
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(name)
    return _circuit_breakers[name]
