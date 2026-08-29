"""
Test suite para resilience patterns.

Verifica que sistema degrada gracefully, nunca falla silenciosamente.
"""

import pytest
from datetime import datetime, timedelta
from app.core.resilience import (
    CircuitBreaker, CircuitBreakerState, RetryConfig, InputValidator, retry_with_exponential_backoff
)


class TestCircuitBreaker:
    """Circuit breaker: previene martillar servicio fallido."""

    def test_circuit_closed_initially(self):
        """Circuit debe estar CLOSED inicialmente."""
        cb = CircuitBreaker("test_service", RetryConfig())
        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.can_attempt()

    def test_circuit_opens_after_threshold(self):
        """Circuit abre después de N fallos."""
        cb = CircuitBreaker("test_service", RetryConfig(failure_threshold=3))
        for _ in range(3):
            cb.record_failure()
        assert cb.state == CircuitBreakerState.OPEN
        assert not cb.can_attempt()

    def test_circuit_half_open_after_timeout(self):
        """Circuit entra en HALF_OPEN después del timeout."""
        cb = CircuitBreaker("test_service", RetryConfig(failure_threshold=2, recovery_timeout=1))
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitBreakerState.OPEN

        # Esperar timeout
        import time
        time.sleep(1.1)

        # can_attempt() triggers the OPEN -> HALF_OPEN transition once
        # recovery_timeout has elapsed
        assert cb.can_attempt()
        assert cb.state == CircuitBreakerState.HALF_OPEN

    def test_circuit_closes_after_successful_test(self):
        """Circuit se cierra después de test exitoso en HALF_OPEN."""
        cb = CircuitBreaker("test_service", RetryConfig(failure_threshold=1, recovery_timeout=1, success_threshold=2))
        cb.record_failure()
        assert cb.state == CircuitBreakerState.OPEN

        import time
        time.sleep(1.1)

        # En HALF_OPEN (can_attempt() drives the transition)
        assert cb.can_attempt()
        assert cb.state == CircuitBreakerState.HALF_OPEN

        # Registrar éxito
        cb.record_success()
        cb.record_success()

        # Debe estar CLOSED
        assert cb.state == CircuitBreakerState.CLOSED


class TestInputValidator:
    """Input validation: rechaza ruido, quarantines dudoso."""

    def test_valid_email(self):
        """Email válido pasa."""
        is_valid, error, rec = InputValidator.validate("email", "user@example.com")
        assert is_valid

    def test_invalid_email(self):
        """Email inválido rechazado."""
        is_valid, error, rec = InputValidator.validate("email", "not-an-email")
        assert not is_valid
        assert error is not None
        assert rec == "reject"

    def test_product_name_too_short(self):
        """Nombre producto muy corto rechazado."""
        is_valid, error, rec = InputValidator.validate("product_name", "ab")
        assert not is_valid

    def test_product_name_valid(self):
        """Nombre producto válido aceptado."""
        is_valid, error, rec = InputValidator.validate("product_name", "Software de accounting")
        assert is_valid

    def test_spam_detection(self):
        """Spam detectado y rechazado."""
        is_valid, error, rec = InputValidator.validate("message", "Buy Viagra now!")
        assert not is_valid
        assert "suspicious" in error.lower()

    def test_batch_validation(self):
        """Validación batch: retorna valid/errors/clean_data."""
        data = {
            "product_name": "My Software",
            "message": "Hola!",
            "email": "invalid-email",
            "price": 100,
        }

        result = InputValidator.validate_batch(data, ["product_name", "message", "email", "price"])

        assert not result["valid"]  # email inválido
        assert "email" in result["errors"]
        assert "product_name" in result["clean_data"]
        assert "message" in result["clean_data"]
        assert "email" not in result["clean_data"]


class TestRetryLogic:
    """Retry con exponential backoff."""

    @pytest.mark.asyncio
    async def test_retry_succeeds_on_second_attempt(self):
        """Retry exitoso en segundo intento."""
        attempt_count = {"count": 0}

        async def flaky_operation():
            attempt_count["count"] += 1
            if attempt_count["count"] < 2:
                raise Exception("Transient error")
            return "success"

        result = await retry_with_exponential_backoff(
            flaky_operation,
            max_retries=3,
            initial_delay=0.01,
            is_idempotent=True
        )

        assert result == "success"
        assert attempt_count["count"] == 2

    @pytest.mark.asyncio
    async def test_non_idempotent_fails_immediately(self):
        """Operación no-idempotente falla en primer intento."""
        attempt_count = {"count": 0}

        async def non_idempotent():
            attempt_count["count"] += 1
            raise Exception("Error")

        with pytest.raises(Exception):
            await retry_with_exponential_backoff(
                non_idempotent,
                max_retries=3,
                is_idempotent=False
            )

        # Solo 1 intento, no reintentos
        assert attempt_count["count"] == 1

    @pytest.mark.asyncio
    async def test_retry_exhaustion(self):
        """Después de N reintentos, falla con último error."""
        async def always_fails():
            raise ValueError("Always fails")

        with pytest.raises(ValueError, match="Always fails"):
            await retry_with_exponential_backoff(
                always_fails,
                max_retries=2,
                initial_delay=0.01,
                is_idempotent=True
            )


class TestGracefulDegradation:
    """Sistema degrada gracefully, nunca falla silenciosamente."""

    def test_circuit_breaker_prevents_cascading_failure(self):
        """Circuit breaker previene cascading failure."""
        cb = CircuitBreaker("failing_service", RetryConfig(failure_threshold=2, recovery_timeout=60))

        # Simular 2 fallos
        cb.record_failure()
        cb.record_failure()

        # Circuit abierto: servicio no disponible
        assert not cb.can_attempt()

        # Otros servicios pueden usar fallback mientras espera
        # (Sin martillar servicio fallido)
        assert cb.state == CircuitBreakerState.OPEN

    def test_input_validation_prevents_garbage_processing(self):
        """Validación previene procesar basura."""
        bad_inputs = [
            ("email", "not-email"),
            ("product_name", "x"),  # Muy corto
            ("message", "Buy Viagra"),  # Spam
            ("phone", "invalid"),
        ]

        for field, value in bad_inputs:
            is_valid, _, _ = InputValidator.validate(field, value)
            assert not is_valid, f"Should reject {field}={value}"

        # Ninguno de estos debería procesarse
        # Sistema limpio, sin spam/basura


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
