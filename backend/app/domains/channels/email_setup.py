"""Guided email connection: detect the provider, explain failures, and confirm with a code.

The person gives an address and a password. Everything else is worked out here:
- the SMTP/IMAP servers come from the address's domain (Gmail, Outlook, Yahoo, iCloud, Zoho), or are guessed;
- a login failure is explained for that provider ("use an app password, here is where to create it");
- once the mailbox logs in, SellIA sends a 6-digit code *through that mailbox, to itself*. Entering the code proves
  the person controls the address and that sending and receiving both work, and only then is the channel connected.
"""

from __future__ import annotations

import hashlib
import hmac
import asyncio
import secrets
import time
from dataclasses import dataclass

CODE_TTL_SECONDS = 15 * 60
RESEND_COOLDOWN_SECONDS = 60
MAX_CODE_ATTEMPTS = 5


@dataclass(frozen=True)
class Provider:
    key: str
    name: str
    smtp_host: str
    smtp_port: int
    imap_host: str
    imap_port: int
    password_help: str
    password_url: str
    guessed: bool = False


_GMAIL = Provider(
    "gmail", "Gmail", "smtp.gmail.com", 587, "imap.gmail.com", 993,
    "Gmail pide una contraseña de aplicación (no tu contraseña normal). Necesitás tener activada la verificación en 2 pasos.",
    "https://myaccount.google.com/apppasswords",
)
_OUTLOOK = Provider(
    "outlook", "Outlook / Hotmail", "smtp-mail.outlook.com", 587, "outlook.office365.com", 993,
    "Outlook pide una contraseña de aplicación. Necesitás tener activada la verificación en dos pasos.",
    "https://account.live.com/proofs/AppPassword",
)
_YAHOO = Provider(
    "yahoo", "Yahoo", "smtp.mail.yahoo.com", 587, "imap.mail.yahoo.com", 993,
    "Yahoo pide una contraseña de aplicación, que se crea en la seguridad de tu cuenta.",
    "https://login.yahoo.com/account/security",
)
_ICLOUD = Provider(
    "icloud", "iCloud", "smtp.mail.me.com", 587, "imap.mail.me.com", 993,
    "iCloud pide una contraseña específica de app, que se crea en tu cuenta de Apple.",
    "https://account.apple.com/account/manage",
)
_ZOHO = Provider(
    "zoho", "Zoho Mail", "smtp.zoho.com", 587, "imap.zoho.com", 993,
    "Zoho pide una contraseña de aplicación, que se crea en la seguridad de tu cuenta.",
    "https://accounts.zoho.com/home#security/app_password",
)

_BY_DOMAIN = {
    "gmail.com": _GMAIL, "googlemail.com": _GMAIL,
    "outlook.com": _OUTLOOK, "outlook.es": _OUTLOOK, "hotmail.com": _OUTLOOK, "hotmail.es": _OUTLOOK,
    "live.com": _OUTLOOK, "msn.com": _OUTLOOK, "outlook.com.ar": _OUTLOOK, "hotmail.com.ar": _OUTLOOK,
    "yahoo.com": _YAHOO, "yahoo.com.ar": _YAHOO, "yahoo.es": _YAHOO, "ymail.com": _YAHOO,
    "icloud.com": _ICLOUD, "me.com": _ICLOUD, "mac.com": _ICLOUD,
    "zoho.com": _ZOHO, "zohomail.com": _ZOHO,
}


def detect_provider(email: str) -> Provider:
    """The provider for an address; for a domain we do not know, the usual ``smtp.``/``imap.`` names."""
    domain = (email or "").rpartition("@")[2].strip().lower()
    known = _BY_DOMAIN.get(domain)
    if known is not None:
        return known
    return Provider(
        "custom", domain or "tu proveedor", f"smtp.{domain}", 587, f"imap.{domain}", 993,
        "Usá la contraseña de esa casilla (o una contraseña de aplicación si tu proveedor la ofrece).",
        "", guessed=True,
    )


def _mx_hosts(domain: str) -> list[str]:
    try:
        import dns.resolver  # transitive dependency of email-validator

        answers = dns.resolver.resolve(domain, "MX", lifetime=4)
        return [str(r.exchange).rstrip(".").lower() for r in sorted(answers, key=lambda r: r.preference)]
    except Exception:  # noqa: BLE001 - no DNS / no MX: fall back to guessing
        return []


async def detect_provider_async(email: str) -> Provider:
    """Like ``detect_provider``, but a custom domain hosted at Google/Microsoft/Zoho gets that provider's settings."""
    provider = detect_provider(email)
    if not provider.guessed:
        return provider
    mx = await asyncio.to_thread(_mx_hosts, provider.name)
    joined = " ".join(mx)
    if "google.com" in joined or "googlemail.com" in joined:
        return _GMAIL
    if "outlook.com" in joined or "protection.outlook" in joined:
        return _OUTLOOK
    if "zoho." in joined:
        return _ZOHO
    return provider


def server_candidates(provider: Provider) -> list[tuple[str, int]]:
    """SMTP servers worth trying: the provider's own, or for a guessed domain the usual names."""
    if not provider.guessed:
        return [(provider.smtp_host, provider.smtp_port)]
    domain = provider.name
    return [(f"smtp.{domain}", 587), (f"mail.{domain}", 587), (f"smtp.{domain}", 465), (f"mail.{domain}", 465)]


def explain_failure(provider: Provider, kind: str, host: str) -> str:
    """What to tell the person when the mailbox would not log in. ``kind``: auth | connect | other."""
    if kind == "auth":
        return f"{provider.name} no aceptó el usuario o la contraseña. {provider.password_help}"
    if kind == "connect":
        if provider.guessed:
            return (
                "No pudimos encontrar el servidor de tu correo automáticamente. Revisá que el email esté bien escrito; "
                "si es de una empresa, pedile a quien administra tu correo los datos de conexión (configuración avanzada)."
            )
        return f"No pudimos conectar con {host}. Probá de nuevo en un momento."
    return "No pudimos verificar la casilla. Probá de nuevo en un momento."


# ── confirmation code ─────────────────────────────────────────────────────
def new_code() -> str:
    return f"{secrets.randbelow(10**6):06d}"


def _digest(secret: str, channel_id: str, code: str) -> str:
    return hmac.new(secret.encode(), f"email-verify|{channel_id}|{code}".encode(), hashlib.sha256).hexdigest()


def pending_verification(secret: str, channel_id: str, code: str, now: float | None = None) -> dict[str, float | int | str]:
    """What is stored about an issued code: only its digest, never the code."""
    now = time.time() if now is None else now
    return {"digest": _digest(secret, channel_id, code), "expires_at": now + CODE_TTL_SECONDS, "sent_at": now, "attempts": 0}


def check_code(secret: str, channel_id: str, stored: dict | None, code: str, now: float | None = None) -> str:
    """'ok' | 'wrong' | 'expired' | 'locked' | 'none'. The caller counts the attempt on 'wrong'."""
    now = time.time() if now is None else now
    if not stored or "digest" not in stored:
        return "none"
    if int(stored.get("attempts", 0)) >= MAX_CODE_ATTEMPTS:
        return "locked"
    if now > float(stored.get("expires_at", 0)):
        return "expired"
    candidate = _digest(secret, channel_id, (code or "").strip())
    return "ok" if hmac.compare_digest(candidate, str(stored["digest"])) else "wrong"


def can_resend(stored: dict | None, now: float | None = None) -> bool:
    now = time.time() if now is None else now
    return not stored or now - float(stored.get("sent_at", 0)) >= RESEND_COOLDOWN_SECONDS
