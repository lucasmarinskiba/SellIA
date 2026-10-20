"""Signup must reject values that are not an email address.

POST /auth/signup used to declare `email: str`, so any string was stored as the
account's email: `test' OR '1'='1@test.local` came back 200, and an address with
CR/LF could reach the verification-email headers. (It was never SQL injection: the
queries are parameterised.) Found by running tests/test_security_auth.py against a
live backend. These checks need no server.
"""

import pytest
from pydantic import ValidationError

from app.api.v1.signup import SignupRequest

PASSWORD = "E2eTest-123!"


def _signup(email: str) -> SignupRequest:
    return SignupRequest(email=email, password=PASSWORD, full_name="Test User")


@pytest.mark.parametrize(
    "email",
    [
        "demo@selia.com",
        "o'brien@example.com",            # apostrophes are legal and real people have them
        "user+tag@example.co.uk",
        "user@test.local",                # special-use domain: what CI and Playwright use
        "e2e-1700000000@test.local",
    ],
)
def test_real_and_test_addresses_are_accepted(email: str) -> None:
    assert _signup(email).email == email


@pytest.mark.parametrize(
    "email",
    [
        "test' OR '1'='1@test.local",     # spaces
        "a@b.com\r\nBcc: victim@example.com",  # header injection
        "a@b.com\nSubject: x",
        "two@@example.com",
        "no-at-sign",
        "missing-dot@localhost",
        "@example.com",
        "user@",
        "with space@example.com",
        "nul\x00byte@example.com",
        "a" * 250 + "@example.com",       # longer than 254
        "",
    ],
)
def test_values_that_are_not_an_address_are_rejected(email: str) -> None:
    with pytest.raises(ValidationError):
        _signup(email)
