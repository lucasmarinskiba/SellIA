"""Security unit tests · password + JWT."""
import jwt
import pytest

from app.core.security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_hash_and_verify_roundtrip():
    h = hash_password("super-secret-pw")
    assert verify_password("super-secret-pw", h)
    assert not verify_password("wrong-pw", h)


def test_hash_is_unique_per_call():
    h1 = hash_password("same-input")
    h2 = hash_password("same-input")
    assert h1 != h2  # bcrypt salts


def test_verify_handles_garbage():
    assert not verify_password("anything", "not-a-bcrypt-hash")


def test_jwt_roundtrip():
    token = create_access_token("user-1", "tenant-1", "owner")
    payload = decode_token(token)
    assert payload["sub"] == "user-1"
    assert payload["tenant_id"] == "tenant-1"
    assert payload["role"] == "owner"


def test_jwt_invalid_signature_raises():
    token = create_access_token("user-1", "tenant-1", "owner")
    tampered = token[:-4] + "AAAA"
    with pytest.raises(jwt.InvalidTokenError):
        decode_token(tampered)
