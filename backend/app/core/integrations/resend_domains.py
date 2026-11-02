"""Resend's domain endpoints: register a business's sending domain, read its DNS records, and ask for verification.

Built against Resend's documented REST API (POST /domains, GET /domains/{id}, POST /domains/{id}/verify). It has not
been exercised against the live service from here; the first real domain is the check.

The API key is RESEND_API_KEY, the same one app/core/email_sender.py uses.
"""

import os
from typing import Any

import httpx

from app.core.logger import get_logger

logger = get_logger(__name__)

RESEND_DOMAINS_URL = "https://api.resend.com/domains"
TIMEOUT_SECONDS = 15.0


class ResendNotConfigured(RuntimeError):
    """RESEND_API_KEY is not set."""


class ResendError(RuntimeError):
    """Resend answered with an error. The message carries no provider detail."""


def _api_key() -> str:
    key = (os.getenv("RESEND_API_KEY") or "").strip()
    if not key:
        raise ResendNotConfigured("RESEND_API_KEY no está configurada")
    return key


async def _request(method: str, url: str, json: dict[str, Any] | None = None) -> dict[str, Any]:
    headers = {"Authorization": f"Bearer {_api_key()}"}
    async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
        response = await client.request(method, url, json=json, headers=headers)
    if response.status_code >= 400:
        logger.warning("Resend %s %s answered %s", method, url, response.status_code)
        raise ResendError(f"Resend respondió {response.status_code}")
    return response.json() if response.content else {}


async def create_domain(name: str) -> dict[str, Any]:
    return await _request("POST", RESEND_DOMAINS_URL, {"name": name})


async def get_domain(domain_id: str) -> dict[str, Any]:
    return await _request("GET", f"{RESEND_DOMAINS_URL}/{domain_id}")


async def verify_domain(domain_id: str) -> None:
    await _request("POST", f"{RESEND_DOMAINS_URL}/{domain_id}/verify")
