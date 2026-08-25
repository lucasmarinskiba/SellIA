"""Tests for security auth endpoints."""

import pytest
import httpx
from uuid import uuid4

BASE_URL = "https://sellia-production.up.railway.app"


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


class TestTwoFactorAuth:
    """Test 2FA endpoints."""

    def test_enable_2fa_returns_qr_code(self, api_client):
        """Enable 2FA returns QR code and secret."""
        user_id = str(uuid4())

        response = api_client.post(
            "/api/v1/auth/2fa/enable",
            json={"user_id": user_id}
        )

        assert response.status_code == 200
        data = response.json()
        assert "secret" in data
        assert "qr_code" in data
        assert data["qr_code"].startswith("data:image/png;base64,")

    def test_enable_2fa_secret_is_base32(self, api_client):
        """2FA secret is valid base32 format."""
        user_id = str(uuid4())

        response = api_client.post(
            "/api/v1/auth/2fa/enable",
            json={"user_id": user_id}
        )

        assert response.status_code == 200
        data = response.json()
        secret = data["secret"]

        # Base32 alphabet: A-Z, 2-7, and padding =
        import re
        assert re.match(r"^[A-Z2-7]+=*$", secret), "Secret not valid base32"

    def test_verify_2fa_with_valid_code(self, api_client):
        """Verify 2FA accepts valid TOTP code."""
        user_id = str(uuid4())

        # Enable 2FA
        enable_response = api_client.post(
            "/api/v1/auth/2fa/enable",
            json={"user_id": user_id}
        )
        secret = enable_response.json()["secret"]

        # Generate valid TOTP code
        import pyotp
        totp = pyotp.TOTP(secret)
        code = totp.now()

        # Verify
        response = api_client.post(
            "/api/v1/auth/2fa/verify",
            json={
                "user_id": user_id,
                "secret": secret,
                "totp_code": code,
            }
        )

        assert response.status_code == 200
        assert response.json()["message"] == "2FA enabled successfully"

    def test_verify_2fa_rejects_invalid_code(self, api_client):
        """Verify 2FA rejects invalid TOTP code."""
        user_id = str(uuid4())

        # Enable 2FA
        enable_response = api_client.post(
            "/api/v1/auth/2fa/enable",
            json={"user_id": user_id}
        )
        secret = enable_response.json()["secret"]

        # Try with invalid code
        response = api_client.post(
            "/api/v1/auth/2fa/verify",
            json={
                "user_id": user_id,
                "secret": secret,
                "totp_code": "000000",
            }
        )

        assert response.status_code == 400

    def test_disable_2fa_requires_password(self, api_client):
        """Disable 2FA requires password confirmation."""
        # First signup
        email = f"test-{uuid4().hex[:8]}@test.local"
        password = "SecurePass123@"
        response = api_client.post(
            "/api/v1/auth/signup",
            json={
                "email": email,
                "password": password,
                "full_name": "Test User",
            }
        )
        user_id = response.json()["user_id"]

        # Try disable without password
        response = api_client.post(
            "/api/v1/auth/2fa/disable",
            json={
                "user_id": user_id,
                "password": "WrongPassword123@",
            }
        )

        assert response.status_code == 401

    def test_disable_2fa_with_correct_password(self, api_client):
        """Disable 2FA with correct password."""
        # Signup
        email = f"test-{uuid4().hex[:8]}@test.local"
        password = "SecurePass123@"
        response = api_client.post(
            "/api/v1/auth/signup",
            json={
                "email": email,
                "password": password,
                "full_name": "Test User",
            }
        )
        user_id = response.json()["user_id"]

        # Disable with correct password
        response = api_client.post(
            "/api/v1/auth/2fa/disable",
            json={
                "user_id": user_id,
                "password": password,
            }
        )

        assert response.status_code == 200
        assert response.json()["message"] == "2FA disabled"


class TestSigninWithTwoFactor:
    """Test signin flow with 2FA."""

    def test_signin_returns_requires_2fa_flag(self, api_client):
        """Signin returns requires_2fa when 2FA is enabled."""
        # Signup
        email = f"test-{uuid4().hex[:8]}@test.local"
        password = "SecurePass123@"
        response = api_client.post(
            "/api/v1/auth/signup",
            json={
                "email": email,
                "password": password,
                "full_name": "Test User",
            }
        )
        user_id = response.json()["user_id"]

        # Enable 2FA
        enable_response = api_client.post(
            "/api/v1/auth/2fa/enable",
            json={"user_id": user_id}
        )
        secret = enable_response.json()["secret"]

        # Verify 2FA
        verify_response = api_client.post(
            "/api/v1/auth/2fa/verify",
            json={
                "user_id": user_id,
                "secret": secret,
                "totp_code": __import__("pyotp").TOTP(secret).now(),
            }
        )
        assert verify_response.status_code == 200

        # Try signin without 2FA code
        signin_response = api_client.post(
            "/api/v1/auth/signin",
            json={
                "email": email,
                "password": password,
            }
        )

        assert signin_response.status_code == 200
        assert signin_response.json().get("requires_2fa") is True

    def test_signin_with_2fa_code_succeeds(self, api_client):
        """Signin succeeds with valid 2FA code."""
        # Signup
        email = f"test-{uuid4().hex[:8]}@test.local"
        password = "SecurePass123@"
        response = api_client.post(
            "/api/v1/auth/signup",
            json={
                "email": email,
                "password": password,
                "full_name": "Test User",
            }
        )
        user_id = response.json()["user_id"]

        # Enable 2FA
        enable_response = api_client.post(
            "/api/v1/auth/2fa/enable",
            json={"user_id": user_id}
        )
        secret = enable_response.json()["secret"]

        # Verify 2FA
        import pyotp
        code = pyotp.TOTP(secret).now()
        verify_response = api_client.post(
            "/api/v1/auth/2fa/verify",
            json={
                "user_id": user_id,
                "secret": secret,
                "totp_code": code,
            }
        )
        assert verify_response.status_code == 200

        # Signin with 2FA code
        new_code = pyotp.TOTP(secret).now()
        signin_response = api_client.post(
            "/api/v1/auth/signin",
            json={
                "email": email,
                "password": password,
                "totp_code": new_code,
            }
        )

        assert signin_response.status_code == 200
        assert "access_token" in signin_response.json()


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
