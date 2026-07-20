"""Computer Use — Action Validator

Valida acciones antes de ejecutarlas para prevenir comportamientos
peligrosos o no deseados: navegación a URLs maliciosas, clicks fuera
de la viewport, inputs excesivos, etc.
"""

import re
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse

from app.core.logger import get_logger
from app.core.config import get_settings

logger = get_logger(__name__)
settings = get_settings()


class ActionValidator:
    """Validador de acciones de Computer Use."""

    # Maximum values
    MAX_CLICK_X = 4096
    MAX_CLICK_Y = 4096
    MAX_TYPE_LENGTH = 10000
    MAX_SCROLL_AMOUNT = 10000
    MAX_WAIT_SECONDS = 60
    MAX_SELECTOR_LENGTH = 2000
    MAX_TEXT_LENGTH = 2000
    MAX_WAIT_TIMEOUT_MS = 60000

    # Allowed keys for press_key (special/navigation keys + single chars).
    ALLOWED_KEYS = {
        "Enter", "Escape", "Tab", "Backspace", "Delete", "Space",
        "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight",
        "Home", "End", "PageUp", "PageDown", "Insert",
    }

    # Dangerous URL patterns
    DANGEROUS_PATTERNS = [
        r"javascript:",
        r"data:text/html",
        r"vbscript:",
        r"file://",
        r"chrome://",
        r"about:config",
    ]

    # Sensitive input patterns (PII)
    SENSITIVE_PATTERNS = [
        r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",  # Credit card
        r"\b\d{3}-\d{2}-\d{4}\b",  # SSN
        r"password\s*=\s*['\"]?[^'\"\s]+",
        r"api[_-]?key\s*=\s*['\"]?[^'\"\s]+",
        r"secret\s*=\s*['\"]?[^'\"\s]+",
    ]

    def __init__(self):
        self.blocked_domains = set(
            settings.COMPUTER_USE_URL_BLACKLIST or []
        )

    def validate_action(
        self,
        action_type: str,
        params: Dict[str, Any],
        current_url: Optional[str] = None,
    ) -> tuple[bool, Optional[str]]:
        """Valida una acción. Retorna (is_valid, error_message)."""

        validators = {
            "navigate": self._validate_navigate,
            "click": self._validate_click,
            "double_click": self._validate_click,
            "right_click": self._validate_click,
            "type": self._validate_type,
            "scroll": self._validate_scroll,
            "wait": self._validate_wait,
            "screenshot": self._validate_screenshot,
            "done": self._validate_done,
            "error": self._validate_error,
            "click_selector": self._validate_click_selector,
            "click_text": self._validate_click_text,
            "fill": self._validate_fill,
            "wait_for_selector": self._validate_wait_for_selector,
            "press_key": self._validate_press_key,
        }

        validator = validators.get(action_type)
        if not validator:
            logger.warning(f"Unknown action type: {action_type}")
            return True, None  # Allow unknown actions with warning

        return validator(params, current_url)

    def _validate_navigate(self, params: Dict[str, Any], current_url: Optional[str]) -> tuple[bool, Optional[str]]:
        url = params.get("url", "")
        if not url:
            return False, "URL vacía para navegación"

        # Check dangerous schemes
        lower_url = url.lower()
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, lower_url):
                return False, f"Esquema URL bloqueado: {pattern}"

        # Check blocked domains
        parsed = urlparse(url)
        hostname = (parsed.hostname or "").lower()
        for blocked in self.blocked_domains:
            if blocked.lower() in hostname:
                return False, f"Dominio bloqueado: {blocked}"

        # Only allow http/https
        if parsed.scheme not in ("http", "https", ""):
            return False, f"Esquema no permitido: {parsed.scheme}"

        return True, None

    def _validate_click(self, params: Dict[str, Any], current_url: Optional[str]) -> tuple[bool, Optional[str]]:
        x = params.get("x")
        y = params.get("y")

        if x is None or y is None:
            return False, "Coordenadas faltantes para click"

        if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
            return False, "Coordenadas deben ser numéricas"

        if x < 0 or x > self.MAX_CLICK_X or y < 0 or y > self.MAX_CLICK_Y:
            return False, f"Coordenadas fuera de rango: ({x}, {y})"

        return True, None

    def _validate_type(self, params: Dict[str, Any], current_url: Optional[str]) -> tuple[bool, Optional[str]]:
        text = params.get("text", "")

        if not text:
            return False, "Texto vacío para typing"

        if len(text) > self.MAX_TYPE_LENGTH:
            return False, f"Texto demasiado largo: {len(text)} > {self.MAX_TYPE_LENGTH}"

        # Check for sensitive data
        for pattern in self.SENSITIVE_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                logger.warning(f"Sensitive data detected in type action (pattern matched)")
                # Don't block, just warn - could be legitimate

        return True, None

    def _validate_scroll(self, params: Dict[str, Any], current_url: Optional[str]) -> tuple[bool, Optional[str]]:
        direction = params.get("direction", "")
        amount = params.get("amount", 0)

        if direction not in ("up", "down", "left", "right"):
            return False, f"Dirección de scroll inválida: {direction}"

        if not isinstance(amount, (int, float)) or amount < 0:
            return False, "Cantidad de scroll debe ser positiva"

        if amount > self.MAX_SCROLL_AMOUNT:
            return False, f"Cantidad de scroll excesiva: {amount}"

        return True, None

    def _validate_wait(self, params: Dict[str, Any], current_url: Optional[str]) -> tuple[bool, Optional[str]]:
        seconds = params.get("seconds", 0)

        if not isinstance(seconds, (int, float)) or seconds < 0:
            return False, "Tiempo de espera inválido"

        if seconds > self.MAX_WAIT_SECONDS:
            return False, f"Tiempo de espera excesivo: {seconds}s > {self.MAX_WAIT_SECONDS}s"

        return True, None

    def _validate_screenshot(self, params: Dict[str, Any], current_url: Optional[str]) -> tuple[bool, Optional[str]]:
        return True, None

    def _validate_done(self, params: Dict[str, Any], current_url: Optional[str]) -> tuple[bool, Optional[str]]:
        return True, None

    def _validate_error(self, params: Dict[str, Any], current_url: Optional[str]) -> tuple[bool, Optional[str]]:
        return True, None

    def _validate_click_selector(self, params: Dict[str, Any], current_url: Optional[str]) -> tuple[bool, Optional[str]]:
        selector = params.get("selector", "")
        if not selector or not isinstance(selector, str) or not selector.strip():
            return False, "Selector vacío para click_selector"
        if len(selector) > self.MAX_SELECTOR_LENGTH:
            return False, f"Selector demasiado largo: {len(selector)} > {self.MAX_SELECTOR_LENGTH}"
        return True, None

    def _validate_click_text(self, params: Dict[str, Any], current_url: Optional[str]) -> tuple[bool, Optional[str]]:
        text = params.get("text", "")
        if not text or not isinstance(text, str) or not text.strip():
            return False, "Texto vacío para click_text"
        if len(text) > self.MAX_TEXT_LENGTH:
            return False, f"Texto demasiado largo: {len(text)} > {self.MAX_TEXT_LENGTH}"
        return True, None

    def _validate_fill(self, params: Dict[str, Any], current_url: Optional[str]) -> tuple[bool, Optional[str]]:
        selector = params.get("selector", "")
        if not selector or not isinstance(selector, str) or not selector.strip():
            return False, "Selector vacío para fill"
        if len(selector) > self.MAX_SELECTOR_LENGTH:
            return False, f"Selector demasiado largo: {len(selector)} > {self.MAX_SELECTOR_LENGTH}"

        value = params.get("value")
        if value is None or not isinstance(value, str):
            return False, "Valor faltante o no textual para fill"
        if len(value) > self.MAX_TYPE_LENGTH:
            return False, f"Valor demasiado largo: {len(value)} > {self.MAX_TYPE_LENGTH}"

        for pattern in self.SENSITIVE_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning("Sensitive data detected in fill action (pattern matched)")

        return True, None

    def _validate_wait_for_selector(self, params: Dict[str, Any], current_url: Optional[str]) -> tuple[bool, Optional[str]]:
        selector = params.get("selector", "")
        if not selector or not isinstance(selector, str) or not selector.strip():
            return False, "Selector vacío para wait_for_selector"
        if len(selector) > self.MAX_SELECTOR_LENGTH:
            return False, f"Selector demasiado largo: {len(selector)} > {self.MAX_SELECTOR_LENGTH}"

        timeout_ms = params.get("timeout_ms")
        if timeout_ms is not None:
            if not isinstance(timeout_ms, (int, float)) or timeout_ms < 0:
                return False, "timeout_ms debe ser positivo"
            if timeout_ms > self.MAX_WAIT_TIMEOUT_MS:
                return False, f"timeout_ms excesivo: {timeout_ms} > {self.MAX_WAIT_TIMEOUT_MS}"

        return True, None

    def _validate_press_key(self, params: Dict[str, Any], current_url: Optional[str]) -> tuple[bool, Optional[str]]:
        key = params.get("key", "")
        if not key or not isinstance(key, str):
            return False, "Tecla vacía para press_key"
        # Permite teclas especiales conocidas, combinaciones (Control+A) y caracteres sueltos.
        if key in self.ALLOWED_KEYS:
            return True, None
        if "+" in key:  # combinación, ej. "Control+A"
            return True, None
        if len(key) == 1:  # carácter único
            return True, None
        return False, f"Tecla no permitida: {key}"

    def validate_batch(self, actions: List[Dict[str, Any]], current_url: Optional[str] = None) -> List[tuple[bool, Optional[str]]]:
        """Valida un lote de acciones."""
        return [self.validate_action(a.get("action_type", ""), a.get("params", {}), current_url) for a in actions]
