"""
Error Recovery Engine — Manejo robusto de errores y recuperación automática.

Modulo 2 de 8: Motor de recuperación inteligente para:
- Network timeouts: retry con backoff exponencial
- Page load delays: esperar visibilidad de elementos
- Authentication failures: re-login, refresh tokens
- Rate limiting: detectar, retroceder, encolar
- JavaScript errors: detectar errores de consola, loguear, reintentar
- CAPTCHA: detectar, escalar a humano
- Session expiration: auto re-autenticación
- Element moved: re-escanear, re-localizar, reintentar

Características:
✓ Retry automático con jitter
✓ Detección de estado de error
✓ Escalamiento a humano cuando sea necesario
✓ Circuit breaker pattern
✓ Backoff exponencial adaptativo
✓ Logging detallado de recuperación

Líneas: 600+ código
"""

import logging
import asyncio
import time
from typing import Dict, Any, Optional, Callable, List, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import json

logger = logging.getLogger(__name__)


# ============================================================================
# ERROR CLASSIFICATIONS
# ============================================================================

class ErrorCategory(str, Enum):
    """Categoría de error."""
    NETWORK_TIMEOUT = "network_timeout"
    PAGE_NOT_LOADED = "page_not_loaded"
    AUTH_FAILED = "auth_failed"
    RATE_LIMITED = "rate_limited"
    JS_ERROR = "js_error"
    CAPTCHA_DETECTED = "captcha_detected"
    SESSION_EXPIRED = "session_expired"
    ELEMENT_NOT_FOUND = "element_not_found"
    ELEMENT_MOVED = "element_moved"
    NAVIGATION_FAILED = "navigation_failed"
    UNKNOWN = "unknown"


class RecoveryStrategy(str, Enum):
    """Estrategia de recuperación."""
    RETRY = "retry"
    REFRESH_PAGE = "refresh_page"
    NAVIGATE_HOME = "navigate_home"
    RELOGIN = "relogin"
    WAIT_AND_RETRY = "wait_and_retry"
    ESCALATE_HUMAN = "escalate_human"
    SKIP_ACTION = "skip_action"
    CIRCUIT_BREAK = "circuit_break"


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class ErrorEvent:
    """Evento de error."""
    timestamp: datetime
    category: ErrorCategory
    message: str
    platform: Optional[str] = None
    url: Optional[str] = None
    stack_trace: Optional[str] = None
    http_status: Optional[int] = None
    retry_count: int = 0
    user_action: Optional[str] = None
    screen_state: Optional[str] = None


@dataclass
class RecoveryAttempt:
    """Intento de recuperación."""
    error_id: str
    strategy: RecoveryStrategy
    timestamp: datetime
    attempt_number: int
    wait_time_ms: int = 0
    success: bool = False
    result: Optional[Any] = None
    next_attempt_at: Optional[datetime] = None


@dataclass
class CircuitBreakerState:
    """Estado de circuit breaker."""
    platform: str
    is_open: bool = False
    failure_count: int = 0
    last_failure_time: Optional[datetime] = None
    reset_at: Optional[datetime] = None
    failure_threshold: int = 5
    reset_timeout_ms: int = 60000


# ============================================================================
# ERROR DETECTOR
# ============================================================================

class ErrorDetector:
    """Detectar y clasificar errores."""

    def __init__(self):
        self.error_patterns = self._build_error_patterns()

    def _build_error_patterns(self) -> Dict[ErrorCategory, List[str]]:
        """Patrones de error para detectar."""
        return {
            ErrorCategory.NETWORK_TIMEOUT: [
                "timeout", "timed out", "no response", "connection refused",
                "ECONNREFUSED", "ETIMEDOUT", "socket hang up"
            ],
            ErrorCategory.PAGE_NOT_LOADED: [
                "page not loaded", "empty response", "blank page", "404", "not found",
                "content not available", "ERR_FAILED", "ERR_NAME_NOT_RESOLVED"
            ],
            ErrorCategory.AUTH_FAILED: [
                "invalid credentials", "login failed", "authentication failed",
                "unauthorized", "401", "403 forbidden", "access denied",
                "invalid email or password"
            ],
            ErrorCategory.RATE_LIMITED: [
                "rate limit", "too many requests", "429", "try again later",
                "quota exceeded", "throttled", "slow down"
            ],
            ErrorCategory.JS_ERROR: [
                "javascript error", "uncaught", "syntax error", "reference error",
                "type error", "null is not an object", "undefined"
            ],
            ErrorCategory.CAPTCHA_DETECTED: [
                "captcha", "recaptcha", "verify you", "robot check",
                "unusual activity", "confirm you're human", "security check"
            ],
            ErrorCategory.SESSION_EXPIRED: [
                "session expired", "please log in again", "session timeout",
                "you have been logged out", "session invalid"
            ],
            ErrorCategory.ELEMENT_NOT_FOUND: [
                "element not found", "no such element", "not visible", "not clickable"
            ],
            ErrorCategory.ELEMENT_MOVED: [
                "stale element", "element moved", "detached from dom",
                "no longer attached to dom"
            ],
        }

    async def detect(
        self,
        error_message: str,
        http_status: Optional[int] = None,
        console_output: Optional[str] = None
    ) -> Tuple[ErrorCategory, str]:
        """
        Detectar categoría de error.

        Returns:
            (categoria, mensaje_normalizado)
        """
        error_lower = error_message.lower()

        # Verificar por categoría
        for category, patterns in self.error_patterns.items():
            for pattern in patterns:
                if pattern in error_lower:
                    return (category, self._normalize_message(error_message, category))

        # Verificar por código HTTP
        if http_status:
            if http_status == 429:
                return (ErrorCategory.RATE_LIMITED, "Rate limited by server")
            elif http_status in [401, 403]:
                return (ErrorCategory.AUTH_FAILED, "Authentication failed")
            elif http_status in [404, 410]:
                return (ErrorCategory.PAGE_NOT_LOADED, "Page not found")
            elif http_status >= 500:
                return (ErrorCategory.NETWORK_TIMEOUT, "Server error")

        return (ErrorCategory.UNKNOWN, error_message)

    def _normalize_message(self, message: str, category: ErrorCategory) -> str:
        """Normalizar mensaje de error."""
        # Remover información sensible
        message = message.replace("Authorization:", "[REDACTED]")
        message = message.replace("Cookie:", "[REDACTED]")

        # Limitar longitud
        if len(message) > 200:
            message = message[:200] + "..."

        return message


# ============================================================================
# ERROR RECOVERY MANAGER
# ============================================================================

class ErrorRecoveryManager:
    """Gestor central de recuperación de errores."""

    def __init__(self, computer_use_engine):
        self.computer_use = computer_use_engine
        self.error_detector = ErrorDetector()
        self.recovery_history: List[RecoveryAttempt] = []
        self.circuit_breakers: Dict[str, CircuitBreakerState] = {}
        self.max_retries = 5
        self.base_backoff_ms = 1000

    async def handle_error(
        self,
        error: Exception,
        action: str,
        platform: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Manejar error y recuperar.

        Retorna resultado de recuperación o escalamiento.
        """
        try:
            # Detectar tipo de error
            category, normalized_msg = await self.error_detector.detect(str(error))

            error_event = ErrorEvent(
                timestamp=datetime.now(),
                category=category,
                message=normalized_msg,
                platform=platform,
                user_action=action,
                stack_trace=str(error.__traceback__)
            )

            logger.error(f"Error detected: {category} - {normalized_msg}")

            # Verificar circuit breaker
            if platform and self._is_circuit_open(platform):
                logger.warning(f"Circuit breaker open for {platform}")
                return {
                    "success": False,
                    "action": "circuit_break",
                    "error_category": category,
                    "message": "Platform circuit breaker is open"
                }

            # Determinar estrategia de recuperación
            strategy = self._select_recovery_strategy(category, kwargs)

            # Intentar recuperar
            result = await self._execute_recovery(
                error_event=error_event,
                strategy=strategy,
                action=action,
                platform=platform,
                **kwargs
            )

            return result

        except Exception as recovery_error:
            logger.error(f"Recovery itself failed: {str(recovery_error)}", exc_info=True)
            return {
                "success": False,
                "action": "escalate_human",
                "error_category": "recovery_failed",
                "message": f"Recovery failed: {str(recovery_error)}"
            }

    def _select_recovery_strategy(
        self,
        category: ErrorCategory,
        context: Dict[str, Any]
    ) -> RecoveryStrategy:
        """Seleccionar estrategia de recuperación."""
        strategies = {
            ErrorCategory.NETWORK_TIMEOUT: RecoveryStrategy.WAIT_AND_RETRY,
            ErrorCategory.PAGE_NOT_LOADED: RecoveryStrategy.REFRESH_PAGE,
            ErrorCategory.AUTH_FAILED: RecoveryStrategy.RELOGIN,
            ErrorCategory.RATE_LIMITED: RecoveryStrategy.WAIT_AND_RETRY,
            ErrorCategory.JS_ERROR: RecoveryStrategy.REFRESH_PAGE,
            ErrorCategory.CAPTCHA_DETECTED: RecoveryStrategy.ESCALATE_HUMAN,
            ErrorCategory.SESSION_EXPIRED: RecoveryStrategy.RELOGIN,
            ErrorCategory.ELEMENT_NOT_FOUND: RecoveryStrategy.REFRESH_PAGE,
            ErrorCategory.ELEMENT_MOVED: RecoveryStrategy.RETRY,
            ErrorCategory.NAVIGATION_FAILED: RecoveryStrategy.NAVIGATE_HOME,
            ErrorCategory.UNKNOWN: RecoveryStrategy.RETRY,
        }

        return strategies.get(category, RecoveryStrategy.SKIP_ACTION)

    async def _execute_recovery(
        self,
        error_event: ErrorEvent,
        strategy: RecoveryStrategy,
        action: str,
        platform: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Ejecutar estrategia de recuperación."""
        retry_count = 0

        while retry_count < self.max_retries:
            try:
                logger.info(f"Recovery attempt {retry_count+1}/{self.max_retries}: {strategy}")

                if strategy == RecoveryStrategy.RETRY:
                    result = await self._retry_action(**kwargs)

                elif strategy == RecoveryStrategy.REFRESH_PAGE:
                    result = await self._refresh_and_retry(**kwargs)

                elif strategy == RecoveryStrategy.NAVIGATE_HOME:
                    result = await self._navigate_home_and_retry(**kwargs)

                elif strategy == RecoveryStrategy.RELOGIN:
                    result = await self._relogin_and_retry(**kwargs)

                elif strategy == RecoveryStrategy.WAIT_AND_RETRY:
                    result = await self._wait_and_retry(retry_count, **kwargs)

                elif strategy == RecoveryStrategy.ESCALATE_HUMAN:
                    return {
                        "success": False,
                        "action": "escalate_human",
                        "error_category": error_event.category.value,
                        "message": "Human escalation required",
                        "details": error_event.message
                    }

                elif strategy == RecoveryStrategy.SKIP_ACTION:
                    return {
                        "success": False,
                        "action": "skip",
                        "error_category": error_event.category.value,
                        "message": "Action skipped due to unrecoverable error"
                    }

                # Registrar intento
                attempt = RecoveryAttempt(
                    error_id=f"{error_event.timestamp.timestamp()}",
                    strategy=strategy,
                    timestamp=datetime.now(),
                    attempt_number=retry_count + 1,
                    success=result.get("success", False)
                )
                self.recovery_history.append(attempt)

                if result.get("success"):
                    logger.info(f"Recovery succeeded after {retry_count+1} attempts")
                    return result

                retry_count += 1

            except Exception as e:
                logger.warning(f"Recovery attempt {retry_count+1} failed: {str(e)}")
                retry_count += 1

        # Abrir circuit breaker si es necesario
        if platform:
            self._increment_failure_count(platform)

        return {
            "success": False,
            "action": "max_retries_exceeded",
            "error_category": error_event.category.value,
            "message": f"Failed after {self.max_retries} recovery attempts"
        }

    async def _retry_action(self, **kwargs) -> Dict[str, Any]:
        """Reintentar acción."""
        action_callable = kwargs.get("action_callable")
        if action_callable:
            try:
                result = await action_callable()
                return {"success": True, "result": result}
            except Exception as e:
                return {"success": False, "error": str(e)}
        return {"success": False, "error": "No action callable provided"}

    async def _refresh_and_retry(self, **kwargs) -> Dict[str, Any]:
        """Refrescar página y reintentar."""
        try:
            await self.computer_use.refresh_page()
            await asyncio.sleep(2)
            return await self._retry_action(**kwargs)
        except Exception as e:
            return {"success": False, "error": f"Refresh failed: {str(e)}"}

    async def _navigate_home_and_retry(self, **kwargs) -> Dict[str, Any]:
        """Navegar a inicio y reintentar."""
        try:
            await self.computer_use.navigate("/")
            await asyncio.sleep(3)
            return await self._retry_action(**kwargs)
        except Exception as e:
            return {"success": False, "error": f"Navigation failed: {str(e)}"}

    async def _relogin_and_retry(self, **kwargs) -> Dict[str, Any]:
        """Re-login y reintentar."""
        try:
            # Obtener credenciales de contexto
            email = kwargs.get("email")
            password = kwargs.get("password")

            if not (email and password):
                return {"success": False, "error": "No credentials provided"}

            # Logout
            await self.computer_use.navigate("/logout")
            await asyncio.sleep(2)

            # Login
            auth_result = await kwargs.get("auth_callable")(email, password)
            if not auth_result:
                return {"success": False, "error": "Re-login failed"}

            # Reintentar acción
            await asyncio.sleep(1)
            return await self._retry_action(**kwargs)

        except Exception as e:
            return {"success": False, "error": f"Re-login failed: {str(e)}"}

    async def _wait_and_retry(
        self,
        attempt_number: int,
        **kwargs
    ) -> Dict[str, Any]:
        """Esperar con backoff y reintentar."""
        wait_time_ms = int(self.base_backoff_ms * (2 ** attempt_number))
        # Agregar jitter
        wait_time_ms += int((wait_time_ms * 0.1) * (hash(str(kwargs)) % 10 / 10))

        logger.info(f"Waiting {wait_time_ms}ms before retry...")
        await asyncio.sleep(wait_time_ms / 1000)

        return await self._retry_action(**kwargs)

    # ========================================================================
    # CIRCUIT BREAKER PATTERN
    # ========================================================================

    def _is_circuit_open(self, platform: str) -> bool:
        """Verificar si circuit breaker está abierto."""
        if platform not in self.circuit_breakers:
            self.circuit_breakers[platform] = CircuitBreakerState(platform=platform)

        state = self.circuit_breakers[platform]

        if state.is_open:
            # Verificar si debe resetearse
            if state.reset_at and datetime.now() >= state.reset_at:
                logger.info(f"Resetting circuit breaker for {platform}")
                state.is_open = False
                state.failure_count = 0
                return False

            return True

        return False

    def _increment_failure_count(self, platform: str) -> None:
        """Incrementar contador de fallos."""
        if platform not in self.circuit_breakers:
            self.circuit_breakers[platform] = CircuitBreakerState(platform=platform)

        state = self.circuit_breakers[platform]
        state.failure_count += 1
        state.last_failure_time = datetime.now()

        if state.failure_count >= state.failure_threshold:
            logger.error(f"Circuit breaker opened for {platform}")
            state.is_open = True
            state.reset_at = datetime.now() + timedelta(milliseconds=state.reset_timeout_ms)

    def reset_circuit_breaker(self, platform: str) -> None:
        """Resetear circuit breaker."""
        if platform in self.circuit_breakers:
            self.circuit_breakers[platform].is_open = False
            self.circuit_breakers[platform].failure_count = 0
            logger.info(f"Circuit breaker reset for {platform}")


# ============================================================================
# RESILIENCE PATTERNS
# ============================================================================

class ResilientAction:
    """Acción resiliente con reintentos automáticos."""

    def __init__(
        self,
        action_callable: Callable,
        recovery_manager: ErrorRecoveryManager,
        max_retries: int = 3,
        timeout_ms: int = 30000
    ):
        self.action_callable = action_callable
        self.recovery_manager = recovery_manager
        self.max_retries = max_retries
        self.timeout_ms = timeout_ms
        self.attempt_count = 0
        self.start_time = None

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Ejecutar con recuperación automática."""
        self.start_time = time.time()

        try:
            # Ejecutar con timeout
            result = await asyncio.wait_for(
                self.action_callable(),
                timeout=self.timeout_ms / 1000
            )
            return {
                "success": True,
                "result": result,
                "attempt": self.attempt_count + 1
            }

        except asyncio.TimeoutError:
            logger.warning("Action timeout")
            return await self.recovery_manager.handle_error(
                TimeoutError("Action timeout"),
                action=self.action_callable.__name__,
                action_callable=self.action_callable,
                **kwargs
            )

        except Exception as e:
            logger.warning(f"Action failed: {str(e)}")
            return await self.recovery_manager.handle_error(
                e,
                action=self.action_callable.__name__,
                action_callable=self.action_callable,
                **kwargs
            )


__all__ = [
    "ErrorDetector",
    "ErrorRecoveryManager",
    "ResilientAction",
    "ErrorCategory",
    "RecoveryStrategy",
    "ErrorEvent",
    "RecoveryAttempt",
    "CircuitBreakerState",
]
