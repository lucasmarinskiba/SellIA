"""
Retry Engine — Exponential backoff + circuit breaker pattern.

Flujo:
1. Exponential backoff: 1s → 2s → 4s → 8s → 16s → 30s (max)
2. Max 3 retries por defecto
3. Aplicable a: pagos fallidos, webhook fails, API timeouts
4. Circuit breaker: stop retrying si service está down (5+ failures)
5. Logging completo + métricas
"""

import logging
import asyncio
from typing import Callable, Optional, Any, Dict, List
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import uuid

logger = logging.getLogger(__name__)


class RetryPolicy(Enum):
    """Políticas de retry predefinidas."""
    DEFAULT = "default"  # 3 retries, exp backoff
    AGGRESSIVE = "aggressive"  # 5 retries, faster backoff
    CONSERVATIVE = "conservative"  # 1 retry, longer wait
    PAYMENT = "payment"  # 3 retries, long waits (pagos son críticos)


class CircuitBreakerState(Enum):
    """Estados del circuit breaker."""
    CLOSED = "closed"  # Funcionando normalmente
    OPEN = "open"  # Falló: rechaza nuevas requests
    HALF_OPEN = "half_open"  # Probando si se recuperó


@dataclass
class RetryConfig:
    """Configuración de retry."""
    max_retries: int = 3
    initial_delay: float = 1.0  # segundos
    max_delay: float = 30.0  # segundos (cap)
    exponential_base: float = 2.0  # backoff multiplier
    jitter: bool = True  # agregar randomness
    timeout: float = 30.0  # timeout por intento

    # Circuit breaker
    failure_threshold: int = 5  # fallos para abrir circuit
    recovery_timeout: float = 60.0  # segundos antes de half-open
    success_threshold: int = 2  # éxitos en half-open para cerrar


@dataclass
class RetryAttempt:
    """Información de un intento de retry."""
    attempt_number: int
    delay_seconds: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    error: Optional[str] = None
    status_code: Optional[int] = None


@dataclass
class RetryHistory:
    """Historial de retries para una operación."""
    operation_id: str
    operation_name: str
    attempts: List[RetryAttempt] = field(default_factory=list)
    final_status: str = "pending"  # success, failed, timeout
    final_error: Optional[str] = None
    total_duration: float = 0.0  # segundos


class CircuitBreaker:
    """Implementa circuit breaker pattern."""

    def __init__(self, name: str, config: RetryConfig):
        self.name = name
        self.config = config
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.last_state_change = datetime.utcnow()

    def record_success(self) -> None:
        """Registra éxito."""
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self._close_circuit()
        elif self.state == CircuitBreakerState.CLOSED:
            self.failure_count = 0  # Reset en estado normal

    def record_failure(self) -> None:
        """Registra fallo."""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()

        if self.state == CircuitBreakerState.CLOSED:
            if self.failure_count >= self.config.failure_threshold:
                self._open_circuit()
        elif self.state == CircuitBreakerState.HALF_OPEN:
            self._open_circuit()

    def can_attempt(self) -> bool:
        """Decide si puede intentar operación."""
        if self.state == CircuitBreakerState.CLOSED:
            return True

        if self.state == CircuitBreakerState.OPEN:
            # Intenta recuperación después de recovery_timeout
            if self.last_failure_time:
                elapsed = (datetime.utcnow() - self.last_failure_time).total_seconds()
                if elapsed > self.config.recovery_timeout:
                    self._try_half_open()
                    return True
            return False

        # HALF_OPEN: permite un intento
        return True

    def _open_circuit(self) -> None:
        """Abre el circuit."""
        self.state = CircuitBreakerState.OPEN
        self.last_state_change = datetime.utcnow()
        logger.warning(f"Circuit breaker '{self.name}' OPENED. Failures: {self.failure_count}")

    def _try_half_open(self) -> None:
        """Transita a half-open."""
        self.state = CircuitBreakerState.HALF_OPEN
        self.success_count = 0
        self.last_state_change = datetime.utcnow()
        logger.info(f"Circuit breaker '{self.name}' HALF-OPEN. Testing recovery...")

    def _close_circuit(self) -> None:
        """Cierra el circuit."""
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_state_change = datetime.utcnow()
        logger.info(f"Circuit breaker '{self.name}' CLOSED. Service recovered.")

    def get_status(self) -> Dict[str, Any]:
        """Retorna status del circuit breaker."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "last_state_change": self.last_state_change.isoformat(),
        }


class RetryEngine:
    """Motor de retry con exponential backoff + circuit breaker."""

    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.retry_history: Dict[str, RetryHistory] = {}
        self.default_config = RetryConfig()

    def get_config(self, policy: RetryPolicy = RetryPolicy.DEFAULT) -> RetryConfig:
        """Retorna configuración según política."""
        configs = {
            RetryPolicy.DEFAULT: RetryConfig(max_retries=3),
            RetryPolicy.AGGRESSIVE: RetryConfig(max_retries=5, initial_delay=0.5, exponential_base=1.5),
            RetryPolicy.CONSERVATIVE: RetryConfig(max_retries=1, initial_delay=5.0),
            RetryPolicy.PAYMENT: RetryConfig(max_retries=3, initial_delay=2.0, max_delay=60.0),
        }
        return configs.get(policy, self.default_config)

    async def execute_with_retry(
        self,
        func: Callable,
        *args,
        policy: RetryPolicy = RetryPolicy.DEFAULT,
        operation_name: str = "operation",
        circuit_breaker_name: Optional[str] = None,
        **kwargs,
    ) -> Any:
        """
        Ejecuta función con retry automático.

        Args:
            func: Función async a ejecutar
            args: Argumentos posicionales
            policy: Política de retry
            operation_name: Nombre para logging
            circuit_breaker_name: Nombre del circuit breaker (si None, no usa CB)
            kwargs: Argumentos nombrados

        Returns:
            Resultado de func, o excepción si se agotan retries
        """

        config = self.get_config(policy)
        operation_id = str(uuid.uuid4())
        history = RetryHistory(operation_id=operation_id, operation_name=operation_name)
        start_time = datetime.utcnow()

        # Obtener o crear circuit breaker
        if circuit_breaker_name:
            if circuit_breaker_name not in self.circuit_breakers:
                self.circuit_breakers[circuit_breaker_name] = CircuitBreaker(
                    circuit_breaker_name, config
                )
            circuit_breaker = self.circuit_breakers[circuit_breaker_name]
        else:
            circuit_breaker = None

        logger.info(
            f"Starting retry execution: {operation_name} (id: {operation_id}, policy: {policy.value})"
        )

        for attempt in range(config.max_retries + 1):
            # Circuit breaker check
            if circuit_breaker and not circuit_breaker.can_attempt():
                error_msg = (
                    f"Circuit breaker '{circuit_breaker_name}' is OPEN. Rejecting attempt."
                )
                logger.error(error_msg)
                history.final_status = "circuit_breaker_open"
                history.final_error = error_msg
                self.retry_history[operation_id] = history
                raise RuntimeError(error_msg)

            try:
                logger.debug(f"Attempt {attempt + 1}/{config.max_retries + 1} for {operation_name}")

                # Ejecutar con timeout
                result = await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=config.timeout,
                )

                # Éxito
                elapsed = (datetime.utcnow() - start_time).total_seconds()
                history.final_status = "success"
                history.total_duration = elapsed
                self.retry_history[operation_id] = history

                if circuit_breaker:
                    circuit_breaker.record_success()

                logger.info(
                    f"Operation succeeded: {operation_name} (attempt: {attempt + 1}, "
                    f"duration: {elapsed:.2f}s)"
                )
                return result

            except asyncio.TimeoutError as e:
                error_msg = f"Timeout after {config.timeout}s"
                self._record_attempt(history, attempt, config, error_msg, timeout=True)

            except Exception as e:
                error_msg = str(e)
                status_code = getattr(e, "status_code", None)
                self._record_attempt(history, attempt, config, error_msg, status_code)

            # Determinar si reintentar
            if attempt < config.max_retries:
                delay = self._calculate_delay(attempt, config)
                logger.warning(
                    f"Attempt {attempt + 1} failed for {operation_name}. "
                    f"Retrying in {delay:.1f}s... (error: {error_msg})"
                )
                await asyncio.sleep(delay)
            else:
                # Agotamos retries
                elapsed = (datetime.utcnow() - start_time).total_seconds()
                history.final_status = "failed"
                history.final_error = error_msg
                history.total_duration = elapsed
                self.retry_history[operation_id] = history

                if circuit_breaker:
                    circuit_breaker.record_failure()

                logger.error(
                    f"Operation exhausted retries: {operation_name} "
                    f"(attempts: {config.max_retries + 1}, duration: {elapsed:.2f}s, "
                    f"error: {error_msg})"
                )
                raise

    def _calculate_delay(self, attempt: int, config: RetryConfig) -> float:
        """Calcula delay con exponential backoff + jitter."""
        delay = config.initial_delay * (config.exponential_base ** attempt)
        delay = min(delay, config.max_delay)  # Cap

        if config.jitter:
            # Jitter: ± 10%
            import random
            jitter_factor = random.uniform(0.9, 1.1)
            delay *= jitter_factor

        return delay

    def _record_attempt(
        self,
        history: RetryHistory,
        attempt: int,
        config: RetryConfig,
        error: str,
        status_code: Optional[int] = None,
        timeout: bool = False,
    ) -> None:
        """Registra intento fallido."""
        if attempt < config.max_retries:
            delay = self._calculate_delay(attempt, config)
        else:
            delay = 0.0

        retry_attempt = RetryAttempt(
            attempt_number=attempt + 1,
            delay_seconds=delay,
            error=error,
            status_code=status_code,
        )
        history.attempts.append(retry_attempt)

    def get_history(self, operation_id: str) -> Optional[RetryHistory]:
        """Obtiene historial de una operación."""
        return self.retry_history.get(operation_id)

    def get_circuit_breaker_status(self, name: str) -> Optional[Dict[str, Any]]:
        """Obtiene status de un circuit breaker."""
        cb = self.circuit_breakers.get(name)
        return cb.get_status() if cb else None

    def get_all_circuit_breakers_status(self) -> Dict[str, Dict[str, Any]]:
        """Obtiene status de todos los circuit breakers."""
        return {name: cb.get_status() for name, cb in self.circuit_breakers.items()}

    def clear_history(self, older_than_hours: int = 24) -> int:
        """Limpia historial viejo."""
        cutoff = datetime.utcnow() - timedelta(hours=older_than_hours)
        removed = 0

        for op_id, history in list(self.retry_history.items()):
            if history.attempts and history.attempts[-1].timestamp < cutoff:
                del self.retry_history[op_id]
                removed += 1

        logger.info(f"Cleared {removed} old retry histories")
        return removed


# Instancia global
retry_engine = RetryEngine()


# ========== DECORADOR CONVENIENTE ==========


def retry(
    policy: RetryPolicy = RetryPolicy.DEFAULT,
    circuit_breaker_name: Optional[str] = None,
):
    """Decorador para retry automático en funciones async."""

    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            return await retry_engine.execute_with_retry(
                func,
                *args,
                policy=policy,
                operation_name=func.__name__,
                circuit_breaker_name=circuit_breaker_name,
                **kwargs,
            )

        return wrapper

    return decorator
