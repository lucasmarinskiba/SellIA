"""Encryption utilities using Fernet for reversible encryption.

Used for storing API keys that need to be retrieved later.
"""

import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Derive a Fernet key from the app's secret key
# In production, this should be a dedicated encryption key
SECRET_KEY = os.environ.get("FERNET_SECRET", os.environ.get("SECRET_KEY", "sellia-default-secret-key-change-me"))


def _get_fernet() -> Fernet:
    """Get or create a Fernet instance derived from the secret key."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"sellia-fixed-salt-v1",  # In production, use a proper salt stored in env
        iterations=480000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(SECRET_KEY.encode()))
    return Fernet(key)


_fernet = None


def get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        _fernet = _get_fernet()
    return _fernet


def encrypt_value(value: str) -> str:
    """Encrypt a string value using Fernet."""
    if not value:
        return ""
    f = get_fernet()
    return f.encrypt(value.encode()).decode()


def decrypt_value(encrypted: str) -> str:
    """Decrypt a Fernet-encrypted string."""
    if not encrypted:
        return ""
    f = get_fernet()
    return f.decrypt(encrypted.encode()).decode()
