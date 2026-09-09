"""Safe server-side fetching of user-supplied URLs.

These URLs come from account holders and are fetched BY THE SERVER, which makes
this a classic SSRF surface: left unguarded, "https://…" could be pointed at
169.254.169.254 (cloud metadata), at 127.0.0.1 (this API itself), or at a
Railway-internal hostname, and the response would be handed back to the caller.

So every hop is validated, not just the first one: redirects are followed
manually and each new location is re-checked against the same rules. Responses
are capped in size and time, and only http/https is ever spoken.
"""

from __future__ import annotations

import ipaddress
import socket
import time
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse, urlunparse

import httpx

from app.core.logger import get_logger

logger = get_logger(__name__)

MAX_REDIRECTS = 5
MAX_BYTES = 2_000_000          # 2 MB of HTML is already far past any real page
TIMEOUT_SECONDS = 10.0
USER_AGENT = (
    "Mozilla/5.0 (compatible; SellIABot/1.0; +https://sellia-brain.vercel.app) "
    "seo-audit"
)


class UnsafeUrlError(ValueError):
    """The URL may not be fetched by the server (bad scheme or private target)."""


def normalize_url(raw: str) -> str:
    """Trim, default to https, and drop any embedded credentials."""
    url = (raw or "").strip()
    if not url:
        raise UnsafeUrlError("URL vacía")
    if "://" not in url:
        url = f"https://{url}"
    parts = urlparse(url)
    if parts.scheme not in ("http", "https"):
        raise UnsafeUrlError(f"Esquema no permitido: {parts.scheme or 'ninguno'}")
    if not parts.hostname:
        raise UnsafeUrlError("La URL no tiene dominio")
    # Strip user:pass@ — credentials in a URL we fetch server-side are never wanted.
    netloc = parts.hostname if parts.port is None else f"{parts.hostname}:{parts.port}"
    return urlunparse((parts.scheme, netloc, parts.path or "/", parts.params, parts.query, ""))


def _assert_public_host(url: str) -> None:
    """Resolve the host and refuse anything that is not a public IP."""
    host = urlparse(url).hostname
    if not host:
        raise UnsafeUrlError("La URL no tiene dominio")
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror as e:
        raise UnsafeUrlError(f"No se pudo resolver el dominio: {host}") from e

    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        ):
            raise UnsafeUrlError(
                f"El dominio {host} apunta a una dirección interna ({ip}) y no se puede analizar."
            )


@dataclass
class FetchResult:
    url: str                      # what we were asked for (normalized)
    final_url: str                # after redirects
    status: Optional[int]
    elapsed_ms: int
    content: str                  # decoded body ('' on failure)
    content_bytes: int
    content_type: str
    error: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.error is None and self.status is not None and 200 <= self.status < 300


async def fetch(raw_url: str) -> FetchResult:
    """Fetch a URL, validating every redirect hop. Never raises for network
    problems -- a failed fetch is a real, reportable result, not an exception."""
    started = time.perf_counter()
    try:
        url = normalize_url(raw_url)
    except UnsafeUrlError as e:
        return FetchResult(raw_url, raw_url, None, 0, "", 0, "", str(e))

    current = url
    try:
        async with httpx.AsyncClient(
            follow_redirects=False,
            timeout=TIMEOUT_SECONDS,
            headers={"User-Agent": USER_AGENT, "Accept": "text/html,*/*"},
        ) as client:
            for _ in range(MAX_REDIRECTS + 1):
                _assert_public_host(current)
                response = await client.get(current)

                if response.is_redirect:
                    location = response.headers.get("location")
                    if not location:
                        break
                    current = normalize_url(str(httpx.URL(current).join(location)))
                    continue

                body = response.content[:MAX_BYTES]
                elapsed_ms = int((time.perf_counter() - started) * 1000)
                return FetchResult(
                    url=url,
                    final_url=current,
                    status=response.status_code,
                    elapsed_ms=elapsed_ms,
                    content=body.decode(response.encoding or "utf-8", errors="replace"),
                    content_bytes=len(response.content),
                    content_type=response.headers.get("content-type", ""),
                )
            error = "Demasiadas redirecciones"
    except UnsafeUrlError as e:
        error = str(e)
    except httpx.TimeoutException:
        error = f"La página no respondió en {int(TIMEOUT_SECONDS)} segundos"
    except httpx.HTTPError as e:
        error = f"No se pudo conectar: {type(e).__name__}"
    except Exception as e:  # noqa: BLE001
        logger.warning("web_presence.fetch failed for %s: %s", raw_url[:120], str(e)[:200])
        error = "No se pudo analizar la URL"

    return FetchResult(
        url=url,
        final_url=current,
        status=None,
        elapsed_ms=int((time.perf_counter() - started) * 1000),
        content="",
        content_bytes=0,
        content_type="",
        error=error,
    )
