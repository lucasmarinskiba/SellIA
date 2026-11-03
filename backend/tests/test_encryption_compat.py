"""Data already encrypted in the database must still decrypt after a cryptography upgrade.

Credentials and API keys are stored as Fernet tokens. The vectors below were produced with cryptography 41.0.7
(the version production pinned before) from fixed secrets; if a newer release changed the PBKDF2 derivation or the
Fernet format, every stored credential would become unreadable. These tests would catch that.
"""

import base64
import hashlib

import pytest
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.core import encryption

SECRET = "compat-fernet-secret-0123456789abcdef"

# app/core/encryption.py: PBKDF2-HMAC-SHA256, 480000 iterations, fixed salt
PBKDF2_KEY = "v_RSVgtcuGZgDbJbwZrlm_BHHlnTmq90OtdLPIukgJA="
PBKDF2_TOKEN = (
    "gAAAAABq6fwUe7GIeQSMgGaBRrpsNpvPfx5guRxu1RzOQ1XNcOJOOuofPzDjvfyqh9H7Hew_Ybca3hhQLwgkobUtvhBkyi_sFReu0QwtLXbG_Zju3Cn94Hs="
)
# app/core/field_encryption.py: SHA-256 of the secret
SHA_KEY = "-hCWCwTJ8KA4jL0A1I4JeuZ_OIjCeOe5wbBBdNPIMck="
SHA_TOKEN = (
    "gAAAAABq6fwU9X-_OKsK_irM9B2sTDlAMD6MQeruTzwOxEmZHzTjIh8UtH5dQjvcn6qqWoDlmC9bDFvzVc37-1-RkOQf8S8XWJEyBXB0d9F8H7Z0CwMooOE="
)


@pytest.fixture
def fixed_secret(monkeypatch):
    monkeypatch.setattr(encryption, "SECRET_KEY", SECRET)
    monkeypatch.setattr(encryption, "_fernet", None)
    yield
    encryption._fernet = None


def test_pbkdf2_derivation_is_unchanged():
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=b"sellia-fixed-salt-v1", iterations=480000)
    assert base64.urlsafe_b64encode(kdf.derive(SECRET.encode())).decode() == PBKDF2_KEY


def test_app_encryption_decrypts_values_stored_by_the_old_version(fixed_secret):
    assert encryption.decrypt_value(PBKDF2_TOKEN) == "token-secreto-de-api"


def test_app_encryption_roundtrip(fixed_secret):
    token = encryption.encrypt_value("otro-secreto")
    assert token != "otro-secreto" and encryption.decrypt_value(token) == "otro-secreto"


def test_field_encryption_key_derivation_and_old_tokens():
    key = base64.urlsafe_b64encode(hashlib.sha256(SECRET.encode()).digest()[:32].ljust(32, b"0")).decode()
    assert key == SHA_KEY
    assert Fernet(SHA_KEY).decrypt(SHA_TOKEN).decode() == "credencial-de-canal"


def test_a_wrong_key_still_fails_closed():
    with pytest.raises(InvalidToken):
        Fernet(PBKDF2_KEY).decrypt(SHA_TOKEN)
