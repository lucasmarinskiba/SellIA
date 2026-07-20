"""
Field Encryption Service

Cifra datos sensibles en la base de datos usando Fernet (AES-128-CBC).
"""

from cryptography.fernet import Fernet
import hashlib
import base64
from typing import Optional

import os

from app.core.config import get_settings

settings = get_settings()

# Usar FERNET_SECRET si está definida; si no, fallback a SECRET_KEY.
# Esto permite rotar SECRET_KEY sin perder datos encriptados.
_fernet_secret = os.environ.get("FERNET_SECRET", settings.SECRET_KEY)

# Derivar clave Fernet (debe ser de 32 bytes)
_fernet_key = base64.urlsafe_b64encode(
    hashlib.sha256(_fernet_secret.encode()).digest()[:32].ljust(32, b'0')
)
_fernet = Fernet(_fernet_key)


def encrypt_field(value: str) -> str:
    """Cifra un campo de texto."""
    if not value:
        return value
    return _fernet.encrypt(value.encode()).decode()


def decrypt_field(encrypted: str) -> str:
    """Descifra un campo de texto."""
    if not encrypted:
        return encrypted
    try:
        return _fernet.decrypt(encrypted.encode()).decode()
    except Exception:
        # Si falla, puede ser que ya estaba en texto plano (backward compat)
        return encrypted


def hash_for_search(value: str) -> str:
    """Genera un hash para búsquedas indexadas sin descifrar."""
    return hashlib.sha256(value.lower().strip().encode()).hexdigest()[:32]
