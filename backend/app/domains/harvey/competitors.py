"""Read a competitor's (or the business's own) public site: prices, offers and headlines. Facts only.

Reuses the prospecting fetcher, so every hop is checked against internal addresses, robots.txt is honoured and
the size is capped. Nothing here interprets: the numbers and phrases are what the page says.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx

from app.domains.harvey import discovery
from app.domains.harvey.discovery import DiscoveryError

MAX_PAGES = 4
MAX_PRICES = 12
MAX_OFFERS = 8
MAX_HEADLINES = 10

_PRICE = re.compile(r"(?:US\$|u\$s|usd|ars|eur|€|\$)\s?\d[\d.,]*(?:\s?(?:usd|ars|eur))?", re.IGNORECASE)
_OFFER = re.compile(
    r"oferta|descuento|%\s?off|\d+\s?%|2x1|3x2|env[ií]o gratis|gratis|promo|cuotas|sin inter[eé]s|garant[ií]a|prueba",
    re.IGNORECASE,
)
_PRICE_PAGE = re.compile(r"precio|planes?|pricing|tienda|shop|productos?|ofertas?|promo|catalogo|cat[aá]logo|servicios", re.IGNORECASE)


class _Parser(discovery._PageParser):
    """The prospecting parser plus h1-h3 headings."""

    def __init__(self) -> None:
        super().__init__()
        self.headings: list[str] = []
        self._h: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        super().handle_starttag(tag, attrs)
        if tag in ("h1", "h2", "h3"):
            self._h = []

    def handle_endtag(self, tag: str) -> None:
        super().handle_endtag(tag)
        if tag in ("h1", "h2", "h3") and self._h is not None:
            text = " ".join(" ".join(self._h).split())
            if 3 <= len(text) <= 120:
                self.headings.append(text)
            self._h = None

    def handle_data(self, data: str) -> None:
        super().handle_data(data)
        if self._h is not None and data.strip():
            self._h.append(data.strip())


def extract(html: str) -> dict[str, Any]:
    """Prices, offer phrases and headlines found in one page."""
    p = _Parser()
    try:
        p.feed(html)
    except Exception:  # noqa: BLE001 - malformed markup: keep what was parsed
        pass
    flat = " ".join(" ".join(p.text).split())
    prices: list[str] = []
    for m in _PRICE.finditer(flat):
        start, end = max(0, m.start() - 40), min(len(flat), m.end() + 20)
        snippet = flat[start:end].strip()
        if snippet not in prices:
            prices.append(snippet)
    offers: list[str] = []
    for sentence in re.split(r"(?<=[.!?])\s+|\s{2,}", flat):
        s = sentence.strip()
        if 8 <= len(s) <= 140 and _OFFER.search(s) and s not in offers:
            offers.append(s)
    return {
        "title": " ".join(p.title.split())[:160],
        "description": (p.meta.get("description") or p.meta.get("og:description") or "")[:300],
        "headlines": list(dict.fromkeys(p.headings))[:MAX_HEADLINES],
        "prices": prices[:MAX_PRICES],
        "offers": offers[:MAX_OFFERS],
        "_links": p.links,
    }


def _price_pages(links: list[tuple[str, str]], base: str, domain: str) -> list[str]:
    out: list[str] = []
    for href, label in links:
        if href.startswith(("mailto:", "tel:", "#", "javascript:")):
            continue
        url = urljoin(base, href).split("#")[0]
        host = urlparse(url).hostname or ""
        if discovery.registrable(host) != domain or url in out:
            continue
        if _PRICE_PAGE.search(urlparse(url).path) or _PRICE_PAGE.search(label):
            out.append(url)
    return out[: MAX_PAGES - 1]


def _merge(into: dict[str, list[str]], part: dict[str, Any]) -> None:
    for key, cap in (("headlines", MAX_HEADLINES), ("prices", MAX_PRICES), ("offers", MAX_OFFERS)):
        for item in part[key]:
            if item not in into[key] and len(into[key]) < cap:
                into[key].append(item)


async def scan(client: httpx.AsyncClient, raw_url: str) -> dict[str, Any]:
    """Home page plus up to three pages that look like prices/products. Raises DiscoveryError if unreadable."""
    url = discovery.normalize_url(raw_url)
    parts = urlparse(url)
    domain = discovery.registrable(parts.hostname or "")
    root = f"{parts.scheme}://{parts.netloc}"
    if not await discovery.robots_allows(client, root):
        raise DiscoveryError(f"{domain}: robots.txt no permite leer el sitio")
    home = await discovery.fetch(client, root + "/")
    if home.status != 200:
        raise DiscoveryError(f"{domain}: respondió {home.status}")

    first = extract(home.text)
    merged: dict[str, list[str]] = {"headlines": [], "prices": [], "offers": []}
    _merge(merged, first)
    pages = [home.url]
    for page_url in _price_pages(first["_links"], home.url, domain):
        path = urlparse(page_url).path or "/"
        if not await discovery.robots_allows(client, root, path):
            continue
        try:
            page = await discovery.fetch(client, page_url)
        except (DiscoveryError, httpx.HTTPError):
            continue
        if page.status == 200:
            pages.append(page.url)
            _merge(merged, extract(page.text))
    return {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "pages": pages,
        "title": first["title"],
        "description": first["description"],
        **merged,
    }
