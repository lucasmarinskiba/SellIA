"""Opt-in access to a LIVE API for tests that drive a real server over HTTP.

test_security_auth.py and test_e2e_sales_funnel.py sign users up and probe
endpoints on a running server. They used to be hard-wired to production, so every
CI run (and every local run of the suite) created real accounts there, and they
failed with 502 whenever Railway was redeploying. They now run only when
SELLIA_LIVE_API_URL is set, and never against production:

    SELLIA_LIVE_API_URL=http://localhost:8000 pytest tests/test_security_auth.py
"""

import os

import pytest

LIVE_API_URL: str = os.environ.get("SELLIA_LIVE_API_URL", "").rstrip("/")

_PRODUCTION_MARKERS = (
    "sellia-production.up.railway.app",
    "sellia-brain.vercel.app",
    "sellia.app",
)


def _skip_reason() -> str:
    if not LIVE_API_URL:
        return (
            "drives a live API and signs users up; set SELLIA_LIVE_API_URL to a "
            "non-production server to run it"
        )
    if any(marker in LIVE_API_URL for marker in _PRODUCTION_MARKERS):
        return f"refusing to run against production ({LIVE_API_URL})"
    return ""


_REASON = _skip_reason()

requires_live_api = pytest.mark.skipif(bool(_REASON), reason=_REASON)
