"""
Input validation — valida y sanitiza inputs. Rechaza ruido, quarantines dudoso.

Extracted from the original app/core/resilience.py (a plain module) into its
own file so it stops colliding with app/core/resilience/ (the package that
superseded it for retry/circuit-breaker concerns — CircuitBreaker, CircuitState,
retry_with_exponential_backoff, ServiceHealthTracker all now live there).
Same-name file+package under one parent directory is ambiguous in Python's
import system; the package silently won that resolution, leaving this class
unreachable via `from app.core.resilience import InputValidator` in production
and in tests/test_resilience.py. Re-exported from app.core.resilience so that
import path keeps working unchanged.
"""

import re
from typing import Any, Dict, Optional


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
