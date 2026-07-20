"""Retry Engine — Exponential backoff + automatic retries.

Maneja fallos transitorios sin intervención humana.
"""

import logging
import asyncio
from typing import Callable, Any, TypeVar, Optional, Dict
from functools import wraps
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RetryPolicy:
    """Política de reintentos con backoff exponencial."""

    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,  # segundos
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
    ):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter

    def get_delay(self, attempt: int) -> float:
        """Calcula delay con exponential backoff."""
        delay = min(
            self.initial_delay * (self.exponential_base ** attempt),
            self.max_delay,
        )

        if self.jitter:
            import random
            delay *= random.uniform(0.8, 1.2)

        return delay


def retry_with_backoff(
    policy: Optional[RetryPolicy] = None,
    retryable_exceptions: tuple = (Exception,),
) -> Callable:
    """Decorator para reintentos automáticos con backoff."""
    if policy is None:
        policy = RetryPolicy()

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(policy.max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e

                    if attempt < policy.max_retries:
                        delay = policy.get_delay(attempt)
                        logger.warning(
                            f"Attempt {attempt + 1}/{policy.max_retries + 1} failed: {e}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f"All {policy.max_retries + 1} retries exhausted for {func.__name__}")
                        raise

            raise last_exception

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(policy.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e

                    if attempt < policy.max_retries:
                        delay = policy.get_delay(attempt)
                        logger.warning(
                            f"Attempt {attempt + 1}/{policy.max_retries + 1} failed: {e}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                        asyncio.run(asyncio.sleep(delay))
                    else:
                        logger.error(f"All {policy.max_retries + 1} retries exhausted for {func.__name__}")
                        raise

            raise last_exception

        # Detectar si es async
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


class RetryableTask:
    """Tarea con reintentos automáticos."""

    def __init__(
        self,
        task_id: str,
        func: Callable,
        args: tuple = (),
        kwargs: Optional[Dict[str, Any]] = None,
        policy: Optional[RetryPolicy] = None,
    ):
        self.task_id = task_id
        self.func = func
        self.args = args
        self.kwargs = kwargs or {}
        self.policy = policy or RetryPolicy()

        self.attempts = 0
        self.last_error: Optional[str] = None
        self.result: Optional[Any] = None
        self.status = "pending"  # pending, running, success, failed
        self.created_at = datetime.utcnow()
        self.completed_at: Optional[datetime] = None

    async def execute(self) -> bool:
        """Ejecuta tarea con reintentos."""
        for attempt in range(self.policy.max_retries + 1):
            self.attempts = attempt + 1
            self.status = "running"

            try:
                if asyncio.iscoroutinefunction(self.func):
                    self.result = await self.func(*self.args, **self.kwargs)
                else:
                    self.result = self.func(*self.args, **self.kwargs)

                self.status = "success"
                self.completed_at = datetime.utcnow()
                logger.info(f"Task {self.task_id} succeeded on attempt {self.attempts}")
                return True

            except Exception as e:
                self.last_error = str(e)

                if attempt < self.policy.max_retries:
                    delay = self.policy.get_delay(attempt)
                    logger.warning(
                        f"Task {self.task_id} attempt {self.attempts} failed: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    self.status = "failed"
                    self.completed_at = datetime.utcnow()
                    logger.error(f"Task {self.task_id} failed after {self.attempts} attempts: {e}")
                    return False

        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a dict para logging/storage."""
        return {
            "task_id": self.task_id,
            "status": self.status,
            "attempts": self.attempts,
            "last_error": self.last_error,
            "result": str(self.result) if self.result else None,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
