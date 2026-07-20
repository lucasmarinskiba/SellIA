"""
Tests para Retry Engine.

Validar:
1. Exponential backoff funciona
2. Circuit breaker se abre/cierra
3. Max retries se respeta
4. Decorador @retry funciona
"""

import pytest
import asyncio
from datetime import datetime
from retry_engine import (
    RetryEngine,
    RetryPolicy,
    RetryConfig,
    CircuitBreakerState,
    retry,
)


@pytest.mark.asyncio
async def test_successful_execution():
    """Test: Ejecución exitosa sin retries."""
    engine = RetryEngine()

    call_count = 0

    async def success_func():
        nonlocal call_count
        call_count += 1
        return "success"

    result = await engine.execute_with_retry(
        success_func,
        policy=RetryPolicy.DEFAULT,
        operation_name="test_success",
    )

    assert result == "success"
    assert call_count == 1


@pytest.mark.asyncio
async def test_exponential_backoff():
    """Test: Exponential backoff calcula delays correctamente."""
    engine = RetryEngine()
    config = RetryConfig(initial_delay=1.0, exponential_base=2.0, jitter=False)

    delays = []
    for attempt in range(3):
        delay = engine._calculate_delay(attempt, config)
        delays.append(delay)

    # 1.0, 2.0, 4.0
    assert delays[0] == 1.0
    assert delays[1] == 2.0
    assert delays[2] == 4.0


@pytest.mark.asyncio
async def test_max_delay_cap():
    """Test: Delay no excede max_delay."""
    engine = RetryEngine()
    config = RetryConfig(initial_delay=1.0, max_delay=10.0, exponential_base=2.0, jitter=False)

    # Intento 10 con base 2: 1 * 2^10 = 1024, capeado a 10.0
    delay = engine._calculate_delay(10, config)
    assert delay == 10.0


@pytest.mark.asyncio
async def test_retry_on_failure():
    """Test: Reintenta cuando falla."""
    engine = RetryEngine()

    call_count = 0

    async def failing_func():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ValueError("Attempt failed")
        return "success"

    result = await engine.execute_with_retry(
        failing_func,
        policy=RetryPolicy.DEFAULT,
        operation_name="test_retry",
    )

    assert result == "success"
    assert call_count == 3  # 2 fallos + 1 éxito


@pytest.mark.asyncio
async def test_exhaust_retries():
    """Test: Agota retries y lanza excepción."""
    engine = RetryEngine()
    config = RetryConfig(max_retries=2)

    call_count = 0

    async def always_fails():
        nonlocal call_count
        call_count += 1
        raise ValueError("Always fails")

    with pytest.raises(ValueError):
        await engine.execute_with_retry(
            always_fails,
            policy=RetryPolicy.DEFAULT,
            operation_name="test_exhaust",
        )

    assert call_count == 3  # 0, 1, 2 = 3 intentos


@pytest.mark.asyncio
async def test_circuit_breaker_opens():
    """Test: Circuit breaker se abre después de fallos."""
    engine = RetryEngine()
    config = RetryConfig(failure_threshold=3)

    call_count = 0

    async def always_fails():
        nonlocal call_count
        call_count += 1
        raise ValueError("Fail")

    # Registrar 3 fallos
    cb = engine.circuit_breakers.get("test_cb") or engine._get_or_create_cb(
        "test_cb", config
    )

    for _ in range(3):
        cb.record_failure()

    # Circuit breaker debe estar OPEN
    assert cb.state == CircuitBreakerState.OPEN
    assert not cb.can_attempt()


@pytest.mark.asyncio
async def test_circuit_breaker_recovery():
    """Test: Circuit breaker se cierra después de éxitos en half-open."""
    engine = RetryEngine()
    config = RetryConfig(failure_threshold=2, success_threshold=2)

    cb = engine.circuit_breakers.get("test_cb_recovery")
    if not cb:
        from retry_engine import CircuitBreaker
        cb = CircuitBreaker("test_cb_recovery", config)
        engine.circuit_breakers["test_cb_recovery"] = cb

    # Abrir
    cb.record_failure()
    cb.record_failure()
    assert cb.state == CircuitBreakerState.OPEN

    # Intentar half-open (simulando timeout pasado)
    cb.last_failure_time = datetime.utcnow() - __import__("datetime").timedelta(seconds=61)
    cb.can_attempt()  # Esto transita a HALF_OPEN

    assert cb.state == CircuitBreakerState.HALF_OPEN

    # Registrar éxitos
    cb.record_success()
    cb.record_success()

    assert cb.state == CircuitBreakerState.CLOSED


@pytest.mark.asyncio
async def test_retry_history():
    """Test: Historial de retries se guarda."""
    engine = RetryEngine()

    call_count = 0

    async def func_with_retry():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise ValueError("First attempt failed")
        return "success"

    operation_id = None
    result = await engine.execute_with_retry(
        func_with_retry,
        policy=RetryPolicy.DEFAULT,
        operation_name="test_history",
    )

    # El operation_id se genera internamente
    # Verificar que history fue guardada
    assert len(engine.retry_history) > 0

    history = list(engine.retry_history.values())[0]
    assert history.final_status == "success"
    assert len(history.attempts) == 2


@pytest.mark.asyncio
async def test_decorator_retry():
    """Test: Decorador @retry funciona."""

    call_count = 0

    @retry(policy=RetryPolicy.DEFAULT)
    async def decorated_func():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise ValueError("Retry needed")
        return "decorated_success"

    result = await decorated_func()

    assert result == "decorated_success"
    assert call_count == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
