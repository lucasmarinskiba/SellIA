"""SQLAlchemy encrypted column types for PII protection.

Uses Fernet (AES-128-CBC) via app.core.encryption for transparent
column-level encryption at rest.
"""

import json
from typing import Any

from sqlalchemy import TypeDecorator, Text
from sqlalchemy.dialects.postgresql import JSONB

from app.core.encryption import encrypt_value, decrypt_value


class EncryptedString(TypeDecorator):
    """String column that encrypts at rest and decrypts on read."""

    impl = Text
    cache_ok = True

    def process_bind_param(self, value: Any | None, dialect: Any) -> Any:
        if value is None:
            return None
        return encrypt_value(str(value))

    def process_result_value(self, value: Any | None, dialect: Any) -> Any:
        if value is None:
            return None
        try:
            return decrypt_value(value)
        except Exception:
            # Backward compat: may be plain text from before encryption
            return value


class EncryptedJSONB(TypeDecorator):
    """JSONB column that encrypts the JSON string at rest."""

    impl = Text
    cache_ok = True

    def process_bind_param(self, value: Any | None, dialect: Any) -> Any:
        if value is None:
            return None
        json_str = json.dumps(value, default=str)
        return encrypt_value(json_str)

    def process_result_value(self, value: Any | None, dialect: Any) -> Any:
        if value is None:
            return None
        try:
            decrypted = decrypt_value(value)
            return json.loads(decrypted)
        except Exception:
            # Backward compat: may be plain JSON from before encryption
            try:
                return json.loads(value)
            except Exception:
                return value
