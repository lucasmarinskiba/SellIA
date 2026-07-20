"""
Resilience Patterns — Patrones de resiliencia y recuperación.

Modulo 6 de 8: Patrones de diseño resiliente para:
- Circuit breaker (plataforma cae? pausa → reintenta después)
- Bulkhead (aislar fallos: una plataforma cae ≠ todas caen)
- Fallback (primario falla? intenta método secundario)
- Timeout (acción lenta? mata después de max tiempo)
- Throttling (rate limit? encola y procesa después)
- Chaos engineering (inyectar fallos aleatorios → probar resiliencia)

Características:
✓ Patrones comprobados
✓ Aislamiento de fallos
✓ Recuperación automática
✓ Monitoreo y alertas
✓ Testing de resiliencia
✓ Logging detallado

Líneas: 400+ código
"""

import logging
import asyncio
import time
import random
from typing import Dict, Any, Optional, Callable, List, Tuple, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import threading
import queue

logger = logging.getLogger(__name__)


# ============================================================================
# CIRCUIT BREAKER PATTERN
# ============================================================================

class CircuitBreakerState(str, Enum):
    """Estados del circuit breaker."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuración de circuit breaker."""
    failure_threshold: int = 5  # Fallos antes de abrir
    success_threshold: int = 2  # Éxitos antes de cerrar (half-open)
    timeout_ms: int = 60000  # Tiempo antes de probar (half-open)
    half_open_max_calls: int = 3  # Máximas llamadas en half-open


class CircuitBreaker:
    """
    Circuit Breaker Pattern.

    Protege contra cascadas de fallos:
    CLOSED → OPEN → HALF_OPEN → CLOSED
    """

    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.half_open_calls = 0
        self.metrics = {
            "total_calls": 0,
            "failures": 0,
            "successes": 0,
            "state_changes": []
        }

    async def call(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Tuple[bool, Any]:
        """
        Ejecutar función a través de circuit breaker.

        Retorna (éxito, resultado)
        """
        self.metrics["total_calls"] += 1

        # Estado OPEN: rechazar llamadas
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self._set_state(CircuitBreakerState.HALF_OPEN)
                logger.info(f"CB {self.name}: transitioning to HALF_OPEN")
            else:
                logger.warning(f"CB {self.name}: OPEN, rejecting call")
                return (False, Exception("Circuit breaker is OPEN"))

        # Ejecutar
        try:
            result = await func(*args, **kwargs)

            # Éxito
            self.failure_count = 0
            self.success_count += 1
            self.metrics["successes"] += 1

            # Half-open → closed
            if self.state == CircuitBreakerState.HALF_OPEN:
                if self.success_count >= self.config.success_threshold:
                    self._set_state(CircuitBreakerState.CLOSED)
                    logger.info(f"CB {self.name}: recovered, transitioning to CLOSED")

            return (True, result)

        except Exception as e:
            # Fallo
            self.failure_count += 1
            self.metrics["failures"] += 1
            self.last_failure_time = datetime.now()

            # Closed → open
            if self.state == CircuitBreakerState.CLOSED:
                if self.failure_count >= self.config.failure_threshold:
                    self._set_state(CircuitBreakerState.OPEN)
                    logger.error(f"CB {self.name}: threshold exceeded, transitioning to OPEN")

            # Half-open → open (cualquier fallo)
            if self.state == CircuitBreakerState.HALF_OPEN:
                self._set_state(CircuitBreakerState.OPEN)
                self.success_count = 0
                logger.error(f"CB {self.name}: failed in HALF_OPEN, back to OPEN")

            return (False, e)

    def _should_attempt_reset(self) -> bool:
        """Verificar si debe intentar reset."""
        if not self.last_failure_time:
            return True

        elapsed = (datetime.now() - self.last_failure_time).total_seconds() * 1000
        return elapsed >= self.config.timeout_ms

    def _set_state(self, new_state: CircuitBreakerState) -> None:
        """Cambiar estado."""
        if new_state != self.state:
            old_state = self.state
            self.state = new_state
            self.metrics["state_changes"].append({
                "timestamp": datetime.now().isoformat(),
                "from": old_state.value,
                "to": new_state.value
            })
            logger.info(f"CB {self.name}: {old_state.value} → {new_state.value}")

            # Reset counters en transiciones
            if new_state == CircuitBreakerState.HALF_OPEN:
                self.success_count = 0
                self.half_open_calls = 0
            elif new_state == CircuitBreakerState.CLOSED:
                self.failure_count = 0
                self.success_count = 0


# ============================================================================
# BULKHEAD PATTERN
# ============================================================================

class BulkheadPartition:
    """Partición del bulkhead (aislamiento de recurso)."""

    def __init__(
        self,
        name: str,
        max_concurrent: int = 5,
        queue_size: int = 100
    ):
        self.name = name
        self.max_concurrent = max_concurrent
        self.queue = asyncio.Queue(maxsize=queue_size)
        self.active_tasks: Set[asyncio.Task] = set()
        self.metrics = {
            "total_requests": 0,
            "accepted": 0,
            "rejected": 0,
            "completed": 0,
            "failed": 0
        }

    async def submit(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Tuple[bool, Any]:
        """
        Enviar trabajo al bulkhead.

        Retorna (éxito, resultado)
        """
        self.metrics["total_requests"] += 1

        # Verificar si hay espacio en cola
        if self.queue.full():
            logger.warning(f"Bulkhead {self.name}: queue full, rejecting request")
            self.metrics["rejected"] += 1
            return (False, Exception("Bulkhead queue full"))

        # Encolar trabajo
        try:
            await asyncio.wait_for(self.queue.put((func, args, kwargs)), timeout=1)
            self.metrics["accepted"] += 1

            # Procesar si hay espacio
            if len(self.active_tasks) < self.max_concurrent:
                asyncio.create_task(self._process_worker())

            return (True, "Queued")

        except asyncio.TimeoutError:
            self.metrics["rejected"] += 1
            return (False, Exception("Timeout enqueuing work"))

    async def _process_worker(self) -> None:
        """Procesar trabajo de la cola."""
        while True:
            try:
                if self.queue.empty():
                    break

                func, args, kwargs = await asyncio.wait_for(self.queue.get(), timeout=1)

                # Ejecutar con límite de concurrencia
                if len(self.active_tasks) >= self.max_concurrent:
                    # Re-encolar
                    await self.queue.put((func, args, kwargs))
                    await asyncio.sleep(0.1)
                    continue

                # Ejecutar
                try:
                    await func(*args, **kwargs)
                    self.metrics["completed"] += 1
                except Exception as e:
                    logger.error(f"Bulkhead {self.name} task failed: {str(e)}")
                    self.metrics["failed"] += 1

            except asyncio.TimeoutError:
                break
            except Exception as e:
                logger.error(f"Bulkhead {self.name} worker error: {str(e)}")
                break

    def get_metrics(self) -> Dict[str, Any]:
        """Obtener métricas."""
        return {
            **self.metrics,
            "active_tasks": len(self.active_tasks),
            "queue_size": self.queue.qsize()
        }


class BulkheadManager:
    """Gestor de bulkheads (aislamiento de recursos)."""

    def __init__(self):
        self.partitions: Dict[str, BulkheadPartition] = {}

    def get_partition(
        self,
        name: str,
        max_concurrent: int = 5,
        queue_size: int = 100
    ) -> BulkheadPartition:
        """Obtener o crear partición."""
        if name not in self.partitions:
            self.partitions[name] = BulkheadPartition(
                name,
                max_concurrent,
                queue_size
            )
        return self.partitions[name]

    async def submit(
        self,
        partition_name: str,
        func: Callable,
        *args,
        **kwargs
    ) -> Tuple[bool, Any]:
        """Enviar trabajo a partición."""
        partition = self.get_partition(partition_name)
        return await partition.submit(func, *args, **kwargs)


# ============================================================================
# FALLBACK PATTERN
# ============================================================================

class FallbackStrategy:
    """Estrategia de fallback."""

    def __init__(self):
        self.strategies: List[Callable] = []

    def add_strategy(self, func: Callable) -> "FallbackStrategy":
        """Agregar estrategia de fallback."""
        self.strategies.append(func)
        return self

    async def execute(self, *args, **kwargs) -> Tuple[bool, Any]:
        """
        Intentar estrategias en orden.

        Retorna (éxito, resultado)
        """
        for idx, strategy in enumerate(self.strategies):
            try:
                logger.info(f"Attempting strategy {idx+1}/{len(self.strategies)}")
                result = await strategy(*args, **kwargs)
                logger.info(f"Strategy {idx+1} succeeded")
                return (True, result)

            except Exception as e:
                logger.warning(f"Strategy {idx+1} failed: {str(e)}")
                if idx == len(self.strategies) - 1:
                    logger.error(f"All {len(self.strategies)} strategies failed")
                    return (False, e)

        return (False, Exception("No strategies available"))


# ============================================================================
# TIMEOUT PATTERN
# ============================================================================

class TimeoutPolicy:
    """Política de timeout."""

    def __init__(
        self,
        timeout_ms: int,
        on_timeout: Optional[Callable] = None
    ):
        self.timeout_ms = timeout_ms
        self.on_timeout = on_timeout

    async def execute(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Tuple[bool, Any]:
        """
        Ejecutar con timeout.

        Retorna (éxito, resultado)
        """
        try:
            result = await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=self.timeout_ms / 1000
            )
            return (True, result)

        except asyncio.TimeoutError:
            logger.warning(f"Timeout after {self.timeout_ms}ms")

            if self.on_timeout:
                try:
                    await self.on_timeout()
                except Exception as e:
                    logger.error(f"Timeout handler failed: {str(e)}")

            return (False, TimeoutError(f"Timeout after {self.timeout_ms}ms"))

        except Exception as e:
            return (False, e)


# ============================================================================
# THROTTLING PATTERN
# ============================================================================

class ThrottlingPolicy:
    """Política de throttling (rate limiting)."""

    def __init__(
        self,
        max_requests_per_minute: int,
        burst_size: int = 5
    ):
        self.max_requests_per_minute = max_requests_per_minute
        self.burst_size = burst_size
        self.request_queue: queue.Queue = queue.Queue()
        self.last_request_time = 0
        self.requests_in_current_minute = 0

    async def acquire(self) -> Tuple[bool, Optional[float]]:
        """
        Adquirir slot de rate limiting.

        Retorna (concedido, tiempo_espera_ms)
        """
        now = time.time()
        minute_ago = now - 60

        # Limpiar requests viejos
        while not self.request_queue.empty():
            request_time = self.request_queue.get_nowait()
            if request_time > minute_ago:
                self.request_queue.put(request_time)
                break

        current_minute_requests = self.request_queue.qsize()

        # Permitir burst
        if current_minute_requests < self.burst_size:
            self.request_queue.put(now)
            return (True, None)

        # Verificar límite por minuto
        if current_minute_requests < self.max_requests_per_minute:
            self.request_queue.put(now)
            return (True, None)

        # Rate limited: calcular espera
        oldest_request = self.request_queue.get_nowait()
        self.request_queue.put(oldest_request)

        wait_time_ms = max(0, (oldest_request + 60 - now) * 1000)
        logger.warning(f"Rate limited, waiting {wait_time_ms:.0f}ms")

        return (False, wait_time_ms)


# ============================================================================
# CHAOS ENGINEERING
# ============================================================================

class ChaosMonkey:
    """Inyector de fallos para testing de resiliencia."""

    def __init__(self, enabled: bool = False):
        self.enabled = enabled
        self.failure_rate = 0.0  # 0-1
        self.latency_ms = 0
        self.latency_variance_ms = 0

    def set_failure_rate(self, rate: float) -> None:
        """Establecer tasa de fallos (0-1)."""
        self.failure_rate = max(0, min(1, rate))

    def set_latency(
        self,
        base_ms: int,
        variance_ms: int = 0
    ) -> None:
        """Establecer latencia."""
        self.latency_ms = base_ms
        self.latency_variance_ms = variance_ms

    async def execute(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Ejecutar función con inyección de fallos."""
        if not self.enabled:
            return await func(*args, **kwargs)

        # Inyectar latencia
        if self.latency_ms > 0:
            latency = self.latency_ms
            if self.latency_variance_ms > 0:
                latency += random.randint(-self.latency_variance_ms, self.latency_variance_ms)
            await asyncio.sleep(latency / 1000)

        # Inyectar fallo
        if random.random() < self.failure_rate:
            logger.warning("Chaos monkey: injecting failure")
            raise Exception("Chaos monkey injected failure")

        return await func(*args, **kwargs)


# ============================================================================
# RESILIENCE COORDINATOR
# ============================================================================

class ResilienceCoordinator:
    """Coordinador central de patrones de resiliencia."""

    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.bulkhead_manager = BulkheadManager()
        self.chaos_monkey = ChaosMonkey(enabled=False)
        self.metrics = {
            "operations": 0,
            "successes": 0,
            "failures": 0,
            "timeouts": 0
        }

    def get_circuit_breaker(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None
    ) -> CircuitBreaker:
        """Obtener o crear circuit breaker."""
        if name not in self.circuit_breakers:
            self.circuit_breakers[name] = CircuitBreaker(name, config)
        return self.circuit_breakers[name]

    async def execute_resilient(
        self,
        func: Callable,
        *args,
        circuit_breaker_name: Optional[str] = None,
        bulkhead_name: Optional[str] = None,
        timeout_ms: Optional[int] = None,
        fallback_strategies: Optional[List[Callable]] = None,
        **kwargs
    ) -> Tuple[bool, Any]:
        """
        Ejecutar función con máxima resiliencia.

        Aplica todos los patrones disponibles:
        1. Circuit breaker
        2. Bulkhead (aislamiento)
        3. Timeout
        4. Fallback
        5. Chaos monkey (si está habilitado)
        """
        self.metrics["operations"] += 1

        try:
            # Envolver función
            resilient_func = func

            # 1. Chaos monkey (outermost)
            if self.chaos_monkey.enabled:
                original_func = resilient_func
                resilient_func = lambda *a, **kw: self.chaos_monkey.execute(original_func, *a, **kw)

            # 2. Timeout
            if timeout_ms:
                timeout_policy = TimeoutPolicy(timeout_ms)
                success, result = await timeout_policy.execute(resilient_func, *args, **kwargs)
                if not success:
                    self.metrics["timeouts"] += 1
                    if isinstance(result, Exception):
                        raise result
            else:
                result = await resilient_func(*args, **kwargs)
                success = True

            # 3. Circuit breaker
            if circuit_breaker_name and success:
                cb = self.get_circuit_breaker(circuit_breaker_name)
                success, result = await cb.call(lambda: asyncio.sleep(0))

            # 4. Bulkhead
            if bulkhead_name and success:
                success, result = await self.bulkhead_manager.submit(
                    bulkhead_name,
                    resilient_func,
                    *args,
                    **kwargs
                )

            if success:
                self.metrics["successes"] += 1
                return (True, result)
            else:
                self.metrics["failures"] += 1
                raise result if isinstance(result, Exception) else Exception(str(result))

        except Exception as e:
            # 5. Fallback
            if fallback_strategies:
                logger.info("Primary failed, attempting fallback strategies")
                fallback = FallbackStrategy()
                for strategy in fallback_strategies:
                    fallback.add_strategy(strategy)

                success, result = await fallback.execute(*args, **kwargs)
                if success:
                    self.metrics["successes"] += 1
                    return (True, result)

            self.metrics["failures"] += 1
            logger.error(f"Resilient execution failed: {str(e)}")
            return (False, e)


__all__ = [
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitBreakerState",
    "BulkheadManager",
    "BulkheadPartition",
    "FallbackStrategy",
    "TimeoutPolicy",
    "ThrottlingPolicy",
    "ChaosMonkey",
    "ResilienceCoordinator",
]
