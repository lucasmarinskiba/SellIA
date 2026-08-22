"""Unit tests for Resend webhook Svix signature verification.

Pure logic, no DB/Redis needed - runs standalone:
    pytest backend/tests/test_resend_webhook.py -v
"""
import base64
import hashlib
import hmac
import time

import pytest

from app.api.v1.resend_webhook import verify_svix_signature


def _make_secret(raw: bytes = b"test-secret-key-1234567890") -> str:
    return "whsec_" + base64.b64encode(raw).decode()


def _sign(secret: str, svix_id: str, svix_timestamp: str, body: bytes) -> str:
    secret_bytes = base64.b64decode(secret[len("whsec_"):])
    signed_content = f"{svix_id}.{svix_timestamp}.{body.decode()}"
    sig = base64.b64encode(
        hmac.new(secret_bytes, signed_content.encode(), hashlib.sha256).digest()
    ).decode()
    return f"v1,{sig}"


class TestSvixSignatureVerification:
    def test_valid_signature_accepted(self):
        secret = _make_secret()
        body = b'{"type":"email.opened"}'
        svix_id, ts = "msg_1", str(int(time.time()))
        sig = _sign(secret, svix_id, ts, body)
        assert verify_svix_signature(body, svix_id, ts, sig, secret) is True

    def test_tampered_body_rejected(self):
        secret = _make_secret()
        body = b'{"type":"email.opened"}'
        svix_id, ts = "msg_1", str(int(time.time()))
        sig = _sign(secret, svix_id, ts, body)
        assert verify_svix_signature(body + b"tampered", svix_id, ts, sig, secret) is False

    def test_wrong_secret_rejected(self):
        secret = _make_secret()
        wrong_secret = _make_secret(b"a-completely-different-secret")
        body = b'{"type":"email.opened"}'
        svix_id, ts = "msg_1", str(int(time.time()))
        sig = _sign(secret, svix_id, ts, body)
        assert verify_svix_signature(body, svix_id, ts, sig, wrong_secret) is False

    def test_stale_timestamp_rejected(self):
        secret = _make_secret()
        body = b'{"type":"email.opened"}'
        svix_id = "msg_1"
        old_ts = str(int(time.time()) - 3600)  # 1 hour old, > 5 min tolerance
        sig = _sign(secret, svix_id, old_ts, body)
        assert verify_svix_signature(body, svix_id, old_ts, sig, secret) is False

    def test_future_timestamp_rejected(self):
        secret = _make_secret()
        body = b'{"type":"email.opened"}'
        svix_id = "msg_1"
        future_ts = str(int(time.time()) + 3600)
        sig = _sign(secret, svix_id, future_ts, body)
        assert verify_svix_signature(body, svix_id, future_ts, sig, secret) is False

    def test_non_numeric_timestamp_rejected(self):
        secret = _make_secret()
        body = b'{"type":"email.opened"}'
        assert verify_svix_signature(body, "msg_1", "not-a-number", "v1,fake", secret) is False

    def test_malformed_secret_prefix_rejected(self):
        body = b'{"type":"email.opened"}'
        svix_id, ts = "msg_1", str(int(time.time()))
        # secret missing the required "whsec_" prefix
        assert verify_svix_signature(body, svix_id, ts, "v1,fake", "not-a-whsec-secret") is False

    def test_accepts_multiple_space_separated_signatures(self):
        """Svix can send multiple signatures (key rotation); any valid match should pass."""
        secret = _make_secret()
        body = b'{"type":"email.opened"}'
        svix_id, ts = "msg_1", str(int(time.time()))
        real_sig = _sign(secret, svix_id, ts, body)
        combined = f"v1,bogusvalue {real_sig.split(',')[1]}"
        # first candidate wrong version-tagged, but reconstruct properly:
        combined = "v1,bogus " + real_sig
        assert verify_svix_signature(body, svix_id, ts, combined, secret) is True
