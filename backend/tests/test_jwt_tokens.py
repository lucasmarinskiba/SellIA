"""Access tokens (app.core.security) after python-jose -> PyJWT.

python-jose is unmaintained and carries advisories that have no patched release, so the login path moved to
PyJWT. The one thing that must not change is that nobody gets logged out: the REF_* tokens below were minted
by python-jose 3.3.0 (the version production ran) with a fixed secret, and must still verify; and everything that
was rejected before (bad signature, expired, other algorithm, ``alg: none``, garbage) must still be rejected.
"""

import base64
import json
import re
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace

import jwt as pyjwt
import pytest

from app.core import security

SECRET = "compat-secret-key-for-jwt-tests-0123456789abcdef"

# Minted by python-jose 3.3.0 with SECRET: payload {"sub": "user-123", "type": "access", ...}
REF_VALID = (  # exp = 4102444800 (2100-01-01), HS256
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyLTEyMyIsInR5cGUiOiJhY2Nlc3MiLCJleHAiOjQxMDI0NDQ4MDB9."
    "S-Xrj1hJkD9xPEacTwumZcfFqHupVdU2pBhjF_mM0AQ"
)
REF_EXPIRED = (  # exp = 1000000000 (2001)
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyLTEyMyIsInR5cGUiOiJhY2Nlc3MiLCJleHAiOjEwMDAwMDAwMDB9."
    "Hk0cAzZHMCnu-kwHXfRaDiFyOwZSy_cxafOH4o53les"
)
REF_HS512 = (  # valid claims, but signed with another algorithm than the one configured
    "eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyLTEyMyIsInR5cGUiOiJhY2Nlc3MiLCJleHAiOjQxMDI0NDQ4MDB9."
    "xKqTxJRZs7VgItcwsPfilm7aYj2z0eWQtqpM0tKhKCFkF8IDdGQKtQ3CC4tkw3hsPwDBthbDNbZucgUAX8w0Mw"
)
REF_NO_EXP = (  # python-jose accepted this; this app never issues a token without "exp"
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyLTEyMyIsInR5cGUiOiJhY2Nlc3MifQ."
    "HrZWOu9Ptj8dRY93bVFqxrL-ml9_yI7grvQWnLgwAGg"
)
REF_WRONG_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyLTEyMyIsInR5cGUiOiJhY2Nlc3MiLCJleHAiOjQxMDI0NDQ4MDB9."
    "YbJ7_taOpkZKtMNmwFSmug6Eql6xlGWFaOZilp8EGLk"
)


@pytest.fixture(autouse=True)
def _fixed_settings(monkeypatch):
    monkeypatch.setattr(
        security, "_settings",
        SimpleNamespace(SECRET_KEY=SECRET, ALGORITHM="HS256", ACCESS_TOKEN_EXPIRE_MINUTES=60),
    )


def _b64(data: dict) -> str:
    return base64.urlsafe_b64encode(json.dumps(data, separators=(",", ":")).encode()).rstrip(b"=").decode()


def test_tokens_minted_by_python_jose_still_verify():
    claims = security.decode_access_token(REF_VALID)
    assert claims == {"sub": "user-123", "type": "access", "exp": 4102444800}


def test_roundtrip():
    token = security.create_access_token({"sub": "abc", "type": "access"})
    claims = security.decode_access_token(token)
    assert claims["sub"] == "abc" and claims["type"] == "access" and isinstance(claims["exp"], int)


def test_tokens_issued_now_verify_with_pyjwt_directly():
    """The format on the wire is plain HS256 JWT, so the sidecar and backend-mvp can read it too."""
    token = security.create_access_token({"sub": "abc"}, expires_delta=timedelta(minutes=5))
    assert pyjwt.decode(token, SECRET, algorithms=["HS256"])["sub"] == "abc"
    assert pyjwt.get_unverified_header(token) == {"alg": "HS256", "typ": "JWT"}


def test_expired_token_is_rejected():
    assert security.decode_access_token(REF_EXPIRED) is None
    expired = security.create_access_token({"sub": "abc"}, expires_delta=timedelta(seconds=-5))
    assert security.decode_access_token(expired) is None


@pytest.mark.parametrize("token", [REF_WRONG_KEY, REF_HS512], ids=["other-secret", "other-algorithm"])
def test_wrong_signature_or_algorithm_is_rejected(token):
    assert security.decode_access_token(token) is None


def test_token_without_exp_is_rejected():
    assert security.decode_access_token(REF_NO_EXP) is None


def test_tampered_payload_is_rejected():
    header, _payload, signature = REF_VALID.split(".")
    forged = f"{header}.{_b64({'sub': 'admin', 'type': 'access', 'exp': 4102444800})}.{signature}"
    assert security.decode_access_token(forged) is None


def test_alg_none_is_rejected():
    header = _b64({"alg": "none", "typ": "JWT"})
    body = _b64({"sub": "admin", "type": "access", "exp": 4102444800})
    assert security.decode_access_token(f"{header}.{body}.") is None
    assert security.decode_access_token(f"{header}.{body}") is None


@pytest.mark.parametrize("token", ["", "garbage", "a.b.c", "....", None, 123, b"bytes"],
                         ids=["empty", "garbage", "abc", "dots", "none", "int", "bytes"])
def test_garbage_is_rejected_not_raised(token):
    assert security.decode_access_token(token) is None


def test_a_non_string_subject_is_rejected():
    """python-jose refused these too ("Subject must be a string"); callers always send str(user.id)."""
    token = pyjwt.encode({"sub": 123, "exp": 4102444800}, SECRET, algorithm="HS256")
    assert security.decode_access_token(token) is None


def test_python_jose_is_gone():
    """No import of it in the app, no pin in any requirements file (the generated-app templates included)."""
    root = Path(__file__).resolve().parents[2]
    offenders = []
    for path in (root / "backend" / "app").rglob("*.py"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if re.search(r"^\s*(from|import)\s+jose\b", text, re.M) or "python-jose" in text:
            offenders.append(str(path.relative_to(root)))
    for pattern in ("backend/requirements*.txt", "sidecar/requirements*.txt", "requirements*.txt"):
        for path in root.glob(pattern):
            pins = [line.split("#")[0] for line in path.read_text(encoding="utf-8", errors="ignore").splitlines()]
            if any("python-jose" in line for line in pins):  # a comment explaining the swap is fine
                offenders.append(str(path.relative_to(root)))
    sidecar = root / "sidecar" / "main.py"
    if sidecar.exists() and re.search(r"^\s*(from|import)\s+jose\b", sidecar.read_text(encoding="utf-8"), re.M):
        offenders.append("sidecar/main.py")
    assert offenders == []
