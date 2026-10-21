"""Tests for security auth endpoints."""

import pytest
import httpx
from uuid import uuid4

from live_api import LIVE_API_URL as BASE_URL, requires_live_api

# Skipped unless SELLIA_LIVE_API_URL points at a non-production server (see live_api.py).
pytestmark = requires_live_api


@pytest.fixture
def api_client():
    return httpx.Client(base_url=BASE_URL)


class TestPasswordRequirements:
    """Test password validation requirements."""

    def test_signup_requires_8_characters(self, api_client):
        """Password must be at least 8 characters."""
        response = api_client.post(
            "/api/v1/auth/signup",
            json={
                "email": f"test-{uuid4().hex[:8]}@test.local",
                "password": "Short1@",
                "full_name": "Test User",
            }
        )
        assert response.status_code == 422

    def test_signup_requires_uppercase(self, api_client):
        """Password must contain uppercase letter."""
        response = api_client.post(
            "/api/v1/auth/signup",
            json={
                "email": f"test-{uuid4().hex[:8]}@test.local",
                "password": "lowercase123@",
                "full_name": "Test User",
            }
        )
        assert response.status_code == 422

    def test_signup_requires_lowercase(self, api_client):
        """Password must contain lowercase letter."""
        response = api_client.post(
            "/api/v1/auth/signup",
            json={
                "email": f"test-{uuid4().hex[:8]}@test.local",
                "password": "UPPERCASE123@",
                "full_name": "Test User",
            }
        )
        assert response.status_code == 422

    def test_signup_requires_digit(self, api_client):
        """Password must contain digit."""
        response = api_client.post(
            "/api/v1/auth/signup",
            json={
                "email": f"test-{uuid4().hex[:8]}@test.local",
                "password": "NoDigits@pass",
                "full_name": "Test User",
            }
        )
        assert response.status_code == 422

    def test_signup_requires_special_char(self, api_client):
        """Password must contain special character (@+-!#$%)."""
        response = api_client.post(
            "/api/v1/auth/signup",
            json={
                "email": f"test-{uuid4().hex[:8]}@test.local",
                "password": "NoSpecial123",
                "full_name": "Test User",
            }
        )
        assert response.status_code == 422

    def test_signup_accepts_all_special_chars(self, api_client):
        """Password accepts all special characters."""
        special_chars = ["@", "+", "-", "!", "#", "$", "%"]
        for char in special_chars:
            response = api_client.post(
                "/api/v1/auth/signup",
                json={
                    "email": f"test-{uuid4().hex[:8]}@test.local",
                    "password": f"ValidPass123{char}",
                    "full_name": "Test User",
                }
            )
            assert response.status_code == 200, f"Failed with char: {char}"

    def test_signup_strong_password_success(self, api_client):
        """Strong password meets all requirements."""
        response = api_client.post(
            "/api/v1/auth/signup",
            json={
                "email": f"test-{uuid4().hex[:8]}@test.local",
                "password": "SecurePass123@",
                "full_name": "Test User",
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "access_token" in data
        assert data.get("requires_2fa_setup") is True


PASSWORD = "SecurePass123@"


def _signup(api_client):
    """Create a throwaway account; returns (email, user_id, auth headers)."""
    email = f"test-{uuid4().hex[:8]}@test.local"
    response = api_client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": PASSWORD, "full_name": "Test User"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    return email, data["user_id"], {"Authorization": f"Bearer {data['access_token']}"}


def _enable_2fa(api_client, headers):
    """Run the whole enrolment the way the signup screen does; returns the TOTP secret."""
    import pyotp

    setup = api_client.post("/api/v1/auth/2fa/setup", headers=headers)
    assert setup.status_code == 200, setup.text
    secret = setup.json()["secret"]
    verify = api_client.post(
        "/api/v1/auth/2fa/verify",
        params={"code": pyotp.TOTP(secret).now()},
        headers=headers,
    )
    assert verify.status_code == 200, verify.text
    return secret


class TestTwoFactorAuth:
    """2FA enrolment: one authenticated flow, identity from the session token.

    POST /auth/2fa/setup -> secret + QR for the signed-in caller, then
    POST /auth/2fa/verify?code=NNNNNN. The server generates and stores the secret;
    the client never names a user or supplies a secret.
    """

    def test_setup_requires_authentication(self, api_client):
        response = api_client.post("/api/v1/auth/2fa/setup")
        assert response.status_code == 401

    def test_verify_requires_authentication(self, api_client):
        response = api_client.post("/api/v1/auth/2fa/verify", params={"code": "123456"})
        assert response.status_code == 401

    def test_disable_requires_authentication(self, api_client):
        response = api_client.post("/api/v1/auth/2fa/disable", params={"code": "123456"})
        assert response.status_code == 401

    def test_setup_returns_qr_code_and_secret(self, api_client):
        _, _, headers = _signup(api_client)

        response = api_client.post("/api/v1/auth/2fa/setup", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["qr_code"].startswith("data:image/png;base64,")
        assert data["provisioning_uri"].startswith("otpauth://totp/")
        assert data["secret"] in data["provisioning_uri"]

    def test_setup_secret_is_base32(self, api_client):
        import re

        _, _, headers = _signup(api_client)

        secret = api_client.post("/api/v1/auth/2fa/setup", headers=headers).json()["secret"]

        # Base32 alphabet: A-Z, 2-7, and padding =
        assert re.match(r"^[A-Z2-7]+=*$", secret), "Secret not valid base32"

    def test_verify_with_valid_code(self, api_client):
        import pyotp

        _, _, headers = _signup(api_client)
        secret = api_client.post("/api/v1/auth/2fa/setup", headers=headers).json()["secret"]

        response = api_client.post(
            "/api/v1/auth/2fa/verify",
            params={"code": pyotp.TOTP(secret).now()},
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "2FA activado correctamente"
        # Recovery codes are shown once, right here, and the signup screen displays them.
        assert len(data["backup_codes"]) == 8

    def test_verify_rejects_invalid_code(self, api_client):
        _, _, headers = _signup(api_client)
        api_client.post("/api/v1/auth/2fa/setup", headers=headers)

        response = api_client.post(
            "/api/v1/auth/2fa/verify", params={"code": "000000"}, headers=headers
        )

        assert response.status_code == 400

    def test_verify_without_setup_is_rejected(self, api_client):
        _, _, headers = _signup(api_client)

        response = api_client.post(
            "/api/v1/auth/2fa/verify", params={"code": "123456"}, headers=headers
        )

        assert response.status_code == 400

    def test_cannot_enable_2fa_on_someone_elses_account(self, api_client):
        """A client-supplied user_id/secret must never reach another user's account.

        The retired signup-time endpoints took {user_id, secret, totp_code} with no
        session and flipped is_2fa_enabled on ANY account, locking its owner out.
        """
        import pyotp

        victim_email, victim_id, _ = _signup(api_client)
        _, _, attacker_headers = _signup(api_client)
        secret = pyotp.random_base32()

        response = api_client.post(
            "/api/v1/auth/2fa/verify",
            json={
                "user_id": victim_id,
                "secret": secret,
                "totp_code": pyotp.TOTP(secret).now(),
            },
            headers=attacker_headers,
        )

        assert response.status_code == 422  # `code` is a required query parameter
        signin = api_client.post(
            "/api/v1/auth/signin", json={"email": victim_email, "password": PASSWORD}
        )
        assert signin.status_code == 200
        assert "access_token" in signin.json()
        assert signin.json().get("requires_2fa") is not True

    def test_disable_2fa_requires_valid_code(self, api_client):
        _, _, headers = _signup(api_client)
        _enable_2fa(api_client, headers)

        response = api_client.post(
            "/api/v1/auth/2fa/disable", params={"code": "000000"}, headers=headers
        )

        assert response.status_code == 400

    def test_disable_2fa_with_valid_code(self, api_client):
        import pyotp

        email, _, headers = _signup(api_client)
        secret = _enable_2fa(api_client, headers)

        response = api_client.post(
            "/api/v1/auth/2fa/disable",
            params={"code": pyotp.TOTP(secret).now()},
            headers=headers,
        )

        assert response.status_code == 200
        assert response.json()["message"] == "2FA desactivado correctamente"
        signin = api_client.post(
            "/api/v1/auth/signin", json={"email": email, "password": PASSWORD}
        )
        assert "access_token" in signin.json()


class TestSigninWithTwoFactor:
    """Test signin flow with 2FA."""

    def test_signin_returns_requires_2fa_flag(self, api_client):
        """Signin returns requires_2fa when 2FA is enabled."""
        email, _, headers = _signup(api_client)
        _enable_2fa(api_client, headers)

        signin_response = api_client.post(
            "/api/v1/auth/signin", json={"email": email, "password": PASSWORD}
        )

        assert signin_response.status_code == 200
        assert signin_response.json().get("requires_2fa") is True
        assert "access_token" not in signin_response.json()

    def test_signin_with_2fa_code_succeeds(self, api_client):
        """Signin succeeds with valid 2FA code."""
        import pyotp

        email, _, headers = _signup(api_client)
        secret = _enable_2fa(api_client, headers)

        signin_response = api_client.post(
            "/api/v1/auth/signin",
            json={
                "email": email,
                "password": PASSWORD,
                "totp_code": pyotp.TOTP(secret).now(),
            },
        )

        assert signin_response.status_code == 200
        assert "access_token" in signin_response.json()

    def test_signin_with_wrong_2fa_code_fails(self, api_client):
        """A wrong code is rejected even with the right password."""
        email, _, headers = _signup(api_client)
        _enable_2fa(api_client, headers)

        signin_response = api_client.post(
            "/api/v1/auth/signin",
            json={"email": email, "password": PASSWORD, "totp_code": "000000"},
        )

        assert signin_response.status_code == 401


class TestSecurityHeaders:
    """Test security-related headers and responses."""

    def test_passwords_not_logged(self, api_client):
        """Passwords should never appear in response."""
        response = api_client.post(
            "/api/v1/auth/signup",
            json={
                "email": f"test-{uuid4().hex[:8]}@test.local",
                "password": "SecurePass123@",
                "full_name": "Test User",
            }
        )

        response_text = response.text.lower()
        assert "securepass" not in response_text
        assert response.json().get("password") is None

    def test_no_sql_injection_in_email(self, api_client):
        """SQL injection attempts are handled safely."""
        response = api_client.post(
            "/api/v1/auth/signup",
            json={
                "email": "test' OR '1'='1@test.local",
                "password": "SecurePass123@",
                "full_name": "Test User",
            }
        )

        # Should reject invalid email format
        assert response.status_code in [400, 422]
