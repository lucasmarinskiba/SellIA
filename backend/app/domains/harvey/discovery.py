"""Prospect discovery: find businesses, read their public site, collect the contact address they publish.

No model calls: it costs nothing but a few HTTP requests.

What it will and will not do
- It only reads pages the site serves to anyone, honours robots.txt, and sends a clear User-Agent.
- It only keeps an address published on the prospect's OWN domain (a business contact address),
  never a personal mailbox (gmail & co.) and never an address it had to guess.
- Every address is stored as ``scraped``: the gate refuses to send to it until a person verifies it.
- URLs come from users, so every request is checked against private/internal addresses (SSRF).
"""

from __future__ import annotations

import asyncio
import ipaddress
import os
import re
import socket
from dataclasses import dataclass, field
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx

from app.core.logger import get_logger

logger = get_logger(__name__)

USER_AGENT = "SellIA-Prospecting/1.0 (+https://sellia.app; contact via the site owner's opt-out)"
MAX_BYTES = 400_000
MAX_REDIRECTS = 3
MAX_EXTRA_PAGES = 3
TIMEOUT = httpx.Timeout(8.0, connect=5.0)

# Personal mailboxes: never prospected from a scrape.
FREE_MAIL_DOMAINS = frozenset({
    "gmail.com", "googlemail.com", "hotmail.com", "hotmail.es", "outlook.com", "outlook.es", "live.com",
    "yahoo.com", "yahoo.com.ar", "yahoo.es", "icloud.com", "me.com", "msn.com", "aol.com",
    "proton.me", "protonmail.com", "gmx.com", "mail.com",
})
# Not a business to prospect: directories, marketplaces, social networks, reference sites.
SKIP_DOMAINS = frozenset({
    "facebook.com", "instagram.com", "linkedin.com", "twitter.com", "x.com", "youtube.com", "tiktok.com",
    "wikipedia.org", "mercadolibre.com", "mercadolibre.com.ar", "tripadvisor.com", "yelp.com",
    "google.com", "maps.google.com", "pinterest.com", "reddit.com", "amazon.com", "paginasamarillas.com.ar",
    "guiaoleo.com.ar", "booking.com", "airbnb.com", "wix.com", "wordpress.com", "blogspot.com",
})
ROLE_LOCALS = frozenset({
    "info", "contacto", "contact", "hola", "hello", "ventas", "sales", "comercial", "admin", "administracion",
    "soporte", "support", "consultas", "oficina", "office", "reservas", "turnos", "atencion", "mail", "email",
})
_BAD_LOCAL = ("noreply", "no-reply", "donotreply", "mailer-daemon", "postmaster", "abuse", "webmaster")
_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]{1,64}@[A-Za-z0-9\-]+(?:\.[A-Za-z0-9\-]+)*\.[A-Za-z]{2,}")
_CONTACT_HINT = re.compile(r"contact|nosotros|about|quienes|equipo|empresa", re.IGNORECASE)
_ASSET_SUFFIX = (".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".css", ".js")


class DiscoveryError(Exception):
    pass


# ── safe fetching ─────────────────────────────────────────────────────────
async def _resolve_host(host: str) -> list[str]:
    infos = await asyncio.to_thread(socket.getaddrinfo, host, None, 0, socket.SOCK_STREAM)
    return sorted({info[4][0] for info in infos})


# Replaceable in tests so they never touch DNS.
resolve_host = _resolve_host


def _is_public(address: str) -> bool:
    ip = ipaddress.ip_address(address.split("%")[0])
    return not (
        ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved or ip.is_unspecified
    )


def normalize_url(raw: str) -> str:
    """``example.com`` -> ``https://example.com``; anything but http(s) with a host is rejected."""
    raw = (raw or "").strip()
    if not raw:
        raise DiscoveryError("URL vacía")
    if "://" not in raw:
        raw = "https://" + raw
    parts = urlparse(raw)
    if parts.scheme not in ("http", "https") or not parts.hostname:
        raise DiscoveryError(f"URL no válida: {raw[:80]}")
    if parts.username or parts.password:
        raise DiscoveryError("la URL no puede llevar usuario ni contraseña")
    if parts.port not in (None, 80, 443):
        raise DiscoveryError("solo se leen los puertos 80 y 443")
    return raw


async def assert_public_url(url: str) -> None:
    host = urlparse(url).hostname or ""
    try:
        ipaddress.ip_address(host)
        addresses = [host]
    except ValueError:
        try:
            addresses = await resolve_host(host)
        except OSError as e:
            raise DiscoveryError(f"no se pudo resolver {host}") from e
    if not addresses or not all(_is_public(a) for a in addresses):
        raise DiscoveryError(f"{host} no es una dirección pública")


@dataclass
class Page:
    url: str
    status: int
    text: str


async def fetch(client: httpx.AsyncClient, url: str) -> Page:
    """GET with a size cap and manual redirects, re-checking every hop against internal addresses."""
    for _ in range(MAX_REDIRECTS + 1):
        await assert_public_url(url)
        async with client.stream("GET", url, headers={"User-Agent": USER_AGENT}, follow_redirects=False) as resp:
            if resp.status_code in (301, 302, 303, 307, 308) and resp.headers.get("location"):
                url = urljoin(url, resp.headers["location"])
                normalize_url(url)
                continue
            ctype = resp.headers.get("content-type", "")
            if resp.status_code == 200 and ctype and "text" not in ctype and "html" not in ctype:
                return Page(url, resp.status_code, "")
            chunks: list[bytes] = []
            size = 0
            async for chunk in resp.aiter_bytes():
                size += len(chunk)
                chunks.append(chunk)
                if size >= MAX_BYTES:
                    break
            body = b"".join(chunks)[:MAX_BYTES]
            return Page(url, resp.status_code, body.decode(resp.encoding or "utf-8", errors="replace"))
    raise DiscoveryError("demasiadas redirecciones")


async def robots_allows(client: httpx.AsyncClient, root: str, path: str = "/") -> bool:
    """robots.txt decides. Missing (404) means allowed; an unreachable or erroring one means we skip."""
    try:
        page = await fetch(client, urljoin(root, "/robots.txt"))
    except (DiscoveryError, httpx.HTTPError):
        return False
    if page.status == 404 or page.status == 410:
        return True
    if page.status != 200:
        return page.status < 400
    parser = RobotFileParser()
    parser.parse(page.text.splitlines())
    return parser.can_fetch(USER_AGENT, urljoin(root, path))


# ── extraction ────────────────────────────────────────────────────────────
class _PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title = ""
        self._in_title = False
        self.meta: dict[str, str] = {}
        self.links: list[tuple[str, str]] = []
        self._href: str | None = None
        self._anchor_text: list[str] = []
        self.text: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag == "title":
            self._in_title = True
        elif tag == "meta":
            key = (a.get("name") or a.get("property") or "").lower()
            if key and a.get("content"):
                self.meta.setdefault(key, a["content"].strip())
        elif tag == "a" and a.get("href"):
            self._href = a["href"].strip()
            self._anchor_text = []
        elif tag in ("script", "style", "noscript"):
            self._skip += 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False
        elif tag == "a" and self._href is not None:
            self.links.append((self._href, " ".join(self._anchor_text).strip()))
            self._href = None
        elif tag in ("script", "style", "noscript") and self._skip:
            self._skip -= 1

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title += data
        elif not self._skip:
            self.text.append(data)
            if self._href is not None:
                self._anchor_text.append(data.strip())


@dataclass
class FoundEmail:
    email: str
    is_company_inbox: bool
    source_url: str


@dataclass
class Site:
    url: str
    domain: str
    company: str = ""
    description: str = ""
    emails: list[FoundEmail] = field(default_factory=list)


def registrable(host: str) -> str:
    """``www.acme.com.ar`` -> ``acme.com.ar`` (good enough for matching an address to its own site)."""
    host = (host or "").lower().rstrip(".")
    return host.removeprefix("www.")


def _same_site(email_domain: str, site_domain: str) -> bool:
    e, s = registrable(email_domain), registrable(site_domain)
    return e == s or e.endswith("." + s) or s.endswith("." + e)


def is_skippable_domain(domain: str) -> bool:
    d = registrable(domain)
    return any(d == bad or d.endswith("." + bad) for bad in SKIP_DOMAINS)


def extract_emails(html: str, site_domain: str, page_url: str, parsed: _PageParser | None = None) -> list[FoundEmail]:
    """Business addresses on the site's own domain, from mailto: links and visible text."""
    parsed = parsed or _parse(html)
    candidates: list[str] = []
    for href, _ in parsed.links:
        if href.lower().startswith("mailto:"):
            candidates.append(href[7:].split("?")[0])
    candidates += _EMAIL_RE.findall(" ".join(parsed.text))
    found: dict[str, FoundEmail] = {}
    for raw in candidates:
        email = raw.strip().strip(".,;:<>()[]").lower()
        if not _EMAIL_RE.fullmatch(email) or email.endswith(_ASSET_SUFFIX):
            continue
        local, _, domain = email.partition("@")
        if domain in FREE_MAIL_DOMAINS or not _same_site(domain, site_domain):
            continue
        if any(bad in local for bad in _BAD_LOCAL):
            continue
        found.setdefault(email, FoundEmail(email, local in ROLE_LOCALS, page_url))
    return list(found.values())


def _parse(html: str) -> _PageParser:
    parser = _PageParser()
    try:
        parser.feed(html)
    except Exception:
        pass
    return parser


def _company_name(parsed: _PageParser, domain: str) -> str:
    name = parsed.meta.get("og:site_name") or ""
    if not name:
        title = re.sub(r"\s+", " ", parsed.title).strip()
        name = re.split(r"\s[|–—\-:]\s", title)[0] if title else ""
    if not name:
        name = registrable(domain).split(".")[0].title()
    return name[:120]


def _description(parsed: _PageParser) -> str:
    text = parsed.meta.get("description") or parsed.meta.get("og:description") or ""
    return re.sub(r"\s+", " ", text).strip()[:300]


def _candidate_pages(parsed: _PageParser, base: str, domain: str) -> list[str]:
    out: list[str] = []
    for href, label in parsed.links:
        if href.lower().startswith(("mailto:", "tel:", "javascript:", "#")):
            continue
        absolute = urljoin(base, href).split("#")[0]
        parts = urlparse(absolute)
        if parts.scheme not in ("http", "https") or not _same_site(parts.hostname or "", domain):
            continue
        if _CONTACT_HINT.search(parts.path) or _CONTACT_HINT.search(label):
            if absolute not in out and absolute.rstrip("/") != base.rstrip("/"):
                out.append(absolute)
    return out[:MAX_EXTRA_PAGES]


async def scan_site(client: httpx.AsyncClient, raw_url: str) -> Site:
    """Read a site's home and contact-like pages; returns what it publishes (possibly no email)."""
    url = normalize_url(raw_url)
    parts = urlparse(url)
    domain = registrable(parts.hostname or "")
    if is_skippable_domain(domain):
        raise DiscoveryError(f"{domain} no es un negocio a prospectar")
    root = f"{parts.scheme}://{parts.netloc}"
    if not await robots_allows(client, root):
        raise DiscoveryError(f"{domain}: robots.txt no permite leer el sitio")

    home = await fetch(client, root + "/")
    if home.status != 200:
        raise DiscoveryError(f"{domain}: respondió {home.status}")
    parsed = _parse(home.text)
    site = Site(url=root, domain=domain, company=_company_name(parsed, domain), description=_description(parsed))
    site.emails = extract_emails(home.text, domain, home.url, parsed)

    for page_url in _candidate_pages(parsed, home.url, domain):
        if len(site.emails) >= 3:
            break
        path = urlparse(page_url).path or "/"
        if not await robots_allows(client, root, path):
            continue
        try:
            page = await fetch(client, page_url)
        except (DiscoveryError, httpx.HTTPError):
            continue
        if page.status == 200:
            known = {e.email for e in site.emails}
            site.emails += [e for e in extract_emails(page.text, domain, page.url) if e.email not in known]
    return site


def make_client(transport: httpx.AsyncBaseTransport | None = None) -> httpx.AsyncClient:
    return httpx.AsyncClient(timeout=TIMEOUT, transport=transport, headers={"Accept-Language": "es,en;q=0.8"})


# ── search ────────────────────────────────────────────────────────────────
def _search_key() -> str:
    return os.environ.get("BRAVE_SEARCH_API_KEY", "").strip()


def search_available() -> bool:
    return bool(_search_key())


async def search_sites(client: httpx.AsyncClient, query: str, count: int = 10) -> list[str]:
    """Home URLs of the sites a web search returns for ``query`` (Brave Search API)."""
    key = _search_key()
    if not key:
        raise DiscoveryError("falta BRAVE_SEARCH_API_KEY: sin buscador solo se pueden cargar sitios a mano")
    try:
        resp = await client.get(
            "https://api.search.brave.com/res/v1/web/search",
            params={"q": query, "count": min(max(count, 1), 20)},
            headers={"X-Subscription-Token": key, "Accept": "application/json"},
        )
        resp.raise_for_status()
        results = resp.json().get("web", {}).get("results", [])
    except (httpx.HTTPError, ValueError) as e:
        logger.warning("harvey: search failed: %s", type(e).__name__)  # never log the key or full error
        raise DiscoveryError(f"el buscador falló ({type(e).__name__})") from e
    urls: list[str] = []
    for item in results:
        parts = urlparse(str(item.get("url") or ""))
        if parts.scheme not in ("http", "https") or not parts.hostname or is_skippable_domain(parts.hostname):
            continue
        home = f"{parts.scheme}://{parts.netloc}"
        if home not in urls:
            urls.append(home)
    return urls
