"""
SellIA Logging Module

Proporciona logging estructurado con enmascaramiento de datos sensibles.
Reemplaza todos los print() dispersos por logging profesional.
"""

import logging
import sys
import re
from datetime import datetime, timezone


class SensitiveDataFilter(logging.Filter):
    """Filtro que enmascara datos sensibles en los logs."""

    # Patrones a enmascarar
    PATTERNS = {
        "email": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
        "api_key": re.compile(r"(api[_-]?key[=:\s]+)([a-zA-Z0-9_\-]{20,})", re.IGNORECASE),
        "token": re.compile(r"(token[=:\s]+)([a-zA-Z0-9_\-\.]{20,})", re.IGNORECASE),
        "password": re.compile(r"(password[=:\s]+)([^\s&]+)", re.IGNORECASE),
        "secret": re.compile(r"(secret[=:\s]+)([^\s&]+)", re.IGNORECASE),
        "ip": re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b"),
    }

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = self._mask(record.msg)
        if record.args:
            record.args = tuple(self._mask(str(arg)) for arg in record.args)
        return True

    def _mask(self, text: str) -> str:
        # Enmascarar emails → u***@example.com
        text = self.PATTERNS["email"].sub(
            lambda m: f"{m.group(0)[0]}***@{m.group(0).split('@')[1]}", text
        )
        # Enmascarar API keys → api_key=***
        text = self.PATTERNS["api_key"].sub(r"\1***", text)
        # Enmascarar tokens → token=***
        text = self.PATTERNS["token"].sub(r"\1***", text)
        # Enmascarar passwords → password=***
        text = self.PATTERNS["password"].sub(r"\1***", text)
        # Enmascarar secrets → secret=***
        text = self.PATTERNS["secret"].sub(r"\1***", text)
        # Enmascarar IPs parcialmente → 192.168.x.x
        text = self.PATTERNS["ip"].sub(
            lambda m: ".".join(m.group(0).split(".")[:2] + ["x", "x"]), text
        )
        return text


def get_logger(name: str) -> logging.Logger:
    """Obtener un logger configurado para SellIA."""
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        handler.addFilter(SensitiveDataFilter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    return logger
