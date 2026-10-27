"""What a channel connection says about itself without leaking its secrets.

- ``mask_credentials``: the API reports WHICH credentials exist, never their values.
- ``restore_masked``: a client that reads a channel and writes it back must not overwrite real secrets with the mask.
- ``account_from_credentials``: the non-secret identity of the account behind a manually configured channel.
- ``public_account``: the identity stored in ``settings["account"]`` (set when an authorization finishes).
"""

from __future__ import annotations

from typing import Any

MASK = "••••••"
_ACCOUNT_FIELDS = ("id", "name", "detail")


def mask_credentials(credentials: dict[str, Any] | None) -> dict[str, str]:
    return {key: MASK for key, value in (credentials or {}).items() if value not in (None, "")}


def restore_masked(incoming: dict[str, Any], existing: dict[str, Any] | None) -> dict[str, Any]:
    """``incoming`` with every masked value replaced by what is actually stored."""
    stored = existing or {}
    return {key: (stored.get(key) if value == MASK else value) for key, value in incoming.items()}


def account(account_id: str | None = None, name: str | None = None, detail: str | None = None) -> dict[str, str]:
    values = {"id": account_id, "name": name, "detail": detail}
    return {key: str(value).strip()[:200] for key, value in values.items() if value not in (None, "")}


def account_from_credentials(platform: str, credentials: dict[str, Any] | None) -> dict[str, str] | None:
    """Identity of a manually configured channel, taken from the non-secret fields the user typed."""
    creds = credentials or {}
    pick = {
        "email": lambda: account(name=creds.get("from_address") or creds.get("smtp_user"), detail=creds.get("smtp_host")),
        "shopify": lambda: account(name=creds.get("shop_domain")),
        "woocommerce": lambda: account(name=creds.get("site_url")),
        "webchat": lambda: account(name=creds.get("site_domain")),
        "etsy": lambda: account(account_id=creds.get("shop_id")),
        "tiktok_shop": lambda: account(account_id=creds.get("shop_id")),
        "amazon": lambda: account(account_id=creds.get("seller_id") or creds.get("marketplace_id")),
    }.get(platform)
    found = pick() if pick else {}
    return found or None


def public_account(settings: dict[str, Any] | None) -> dict[str, str] | None:
    stored = (settings or {}).get("account")
    if not isinstance(stored, dict):
        return None
    found = {key: str(stored[key]) for key in _ACCOUNT_FIELDS if stored.get(key)}
    return found or None
