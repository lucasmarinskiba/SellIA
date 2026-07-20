"""
Resilience patterns — retry, circuit breaker, input validation.

Sistema nunca cae. Degrada gracefully o falla rápido (no fallar silenciosamente).
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Callable, Any, Optional, Dict
from enum import Enum
import re

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    """Estado de circuit breaker."""
    CLOSED = "closed"  # Normal traffic
    OPEN = "open"      # Failing; rechaza requests
    HALF_OPEN = "half_open"  # Testing si servicio recuperó


class CircuitBreaker:
    """Circuit breaker: previene martillar servicio fallido."""

    def __init__(self, name: str, failure_threshold: int = 5, timeout_seconds: int = 60):
        self.name = name
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.success_count = 0

    def record_success(self):
        """Registra éxito."""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= 2:  # 2 éxitos = vuelve a CLOSED
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
                logger.info(f"[{self.name}] Circuit CLOSED: servicio recuperado")
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0

    def record_failure(self):
        """Registra falla."""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()

        if self.state == CircuitState.CLOSED and self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(f"[{self.name}] Circuit OPEN: {self.failure_count} fallos consecutivos")

        elif self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            logger.warning(f"[{self.name}] Circuit OPEN: fallo durante half-open test")

    def is_available(self) -> bool:
        """¿Puedo intentar request?"""
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            # Chequea si timeout expiró (cambiar a HALF_OPEN)
            if self.last_failure_time and datetime.utcnow() >= self.last_failure_time + timedelta(seconds=self.timeout_seconds):
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
                logger.info(f"[{self.name}] Circuit HALF_OPEN: testeando recuperación")
                return True
            return False

        # HALF_OPEN: permite 1 request de prueba
        return self.state == CircuitState.HALF_OPEN


async def retry_with_exponential_backoff(
    func: Callable,
    args: tuple = (),
    kwargs: dict = None,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    is_idempotent: bool = True
) -> Any:
    """
    Reintenta operación con backoff exponencial.

    - Operaciones idempotentes (envío mensaje): reintenta 3x (1s, 2s, 4s)
    - Operaciones no-idempotentes (crear recurso): fail rápido
    """

    if kwargs is None:
        kwargs = {}

    if not is_idempotent:
        # No reintentar operaciones no-idempotentes
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Non-idempotent operation failed: {str(e)}")
            raise

    delay = initial_delay
    last_exception = None

    for attempt in range(max_retries):
        try:
            result = await func(*args, **kwargs)
            if attempt > 0:
                logger.info(f"Operation succeeded after {attempt + 1} attempts")
            return result
        except Exception as e:
            last_exception = e
            if attempt < max_retries - 1:
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {delay}s...")
                await asyncio.sleep(delay)
                delay *= 2  # Exponential backoff
            else:
                logger.error(f"All {max_retries} attempts failed")

    raise last_exception


class InputValidator:
    """Valida y sanitiza inputs. Rechaza ruido, quarantines dudoso."""

    # Reglas de validación
    RULES = {
        "product_name": {
            "min_length": 3,
            "max_length": 200,
            "pattern": r"^[a-zA-Z0-9\s\-\.áéíóúñ]+$",
        },
        "price": {
            "min_value": 0.01,
            "max_value": 1_000_000,
            "type": "float",
        },
        "email": {
            "pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
        },
        "phone": {
            "pattern": r"^[\d\s\-\(\)\+]{10,20}$",
        },
        "url": {
            "pattern": r"^https?://[a-zA-Z0-9\-._~:/?#\[\]@!$&'()*+,;=]+$",
        },
        "message": {
            "min_length": 1,
            "max_length": 5000,
            "reject_patterns": [r"viagra", r"casino", r"pharma"],  # Spam
        },
    }

    @classmethod
    def validate(cls, field_name: str, value: Any) -> tuple[bool, Optional[str], Optional[str]]:
        """
        Valida field.

        Returns: (is_valid, error_message, recommendation)
        - is_valid: True/False
        - error_message: si invalido, qué regla falló
        - recommendation: "reject" o "quarantine"
        """

        if not value:
            return False, f"{field_name} is required", "reject"

        rules = cls.RULES.get(field_name, {})

        if not rules:
            return True, None, None  # No rules = accept

        # Verificar min/max length
        if "min_length" in rules:
            if len(str(value)) < rules["min_length"]:
                return False, f"{field_name} too short (min {rules['min_length']})", "reject"

        if "max_length" in rules:
            if len(str(value)) > rules["max_length"]:
                return False, f"{field_name} too long (max {rules['max_length']})", "reject"

        # Verificar patrón regex
        if "pattern" in rules:
            if not re.match(rules["pattern"], str(value)):
                return False, f"{field_name} format invalid", "reject"

        # Verificar reject patterns (spam)
        if "reject_patterns" in rules:
            for reject_pattern in rules["reject_patterns"]:
                if re.search(reject_pattern, str(value), re.IGNORECASE):
                    return False, f"{field_name} contains suspicious content", "reject"

        # Verificar tipo
        if rules.get("type") == "float":
            try:
                val = float(value)
                if "min_value" in rules and val < rules["min_value"]:
                    return False, f"{field_name} must be >= {rules['min_value']}", "reject"
                if "max_value" in rules and val > rules["max_value"]:
                    return False, f"{field_name} must be <= {rules['max_value']}", "reject"
            except ValueError:
                return False, f"{field_name} must be a number", "reject"

        return True, None, None

    @classmethod
    def validate_batch(cls, data: Dict[str, Any], fields_to_check: list[str]) -> Dict[str, Any]:
        """
        Valida múltiples fields.

        Returns: {
            "valid": True/False,
            "errors": {"field": "error message"},
            "quarantine": ["field1", "field2"],  # Dudosos
            "clean_data": {field: value}  # Solo datos válidos
        }
        """

        errors = {}
        quarantine = []
        clean_data = {}

        for field in fields_to_check:
            if field not in data:
                continue

            is_valid, error_msg, recommendation = cls.validate(field, data[field])

            if not is_valid:
                if recommendation == "reject":
                    errors[field] = error_msg
                elif recommendation == "quarantine":
                    quarantine.append(field)
            else:
                clean_data[field] = data[field]

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "quarantine": quarantine,
            "clean_data": clean_data,
        }


class ServiceHealthTracker:
    """Rastrear salud de servicios externos (API fallas, latencia)."""

    def __init__(self):
        self.services: Dict[str, CircuitBreaker] = {}

    def get_breaker(self, service_name: str) -> CircuitBreaker:
        """Obtiene o crea circuit breaker para servicio."""
        if service_name not in self.services:
            self.services[service_name] = CircuitBreaker(service_name)
        return self.services[service_name]

    def is_service_available(self, service_name: str) -> bool:
        """¿Servicio está disponible?"""
        breaker = self.get_breaker(service_name)
        return breaker.is_available()

    def record_success(self, service_name: str):
        """Marca servicio como ok."""
        self.get_breaker(service_name).record_success()

    def record_failure(self, service_name: str):
        """Marca servicio como fallido."""
        self.get_breaker(service_name).record_failure()

    def status(self) -> Dict[str, str]:
        """Status de todos los servicios."""
        return {name: breaker.state.value for name, breaker in self.services.items()}


# Global instance
health_tracker = ServiceHealthTracker()
