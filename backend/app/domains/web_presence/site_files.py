"""robots.txt and sitemap.xml, actually fetched and actually parsed.

A perfect page that robots.txt disallows ranks nowhere, and a store with no
sitemap makes Google discover its product pages by luck. Both files are public,
free to read and decisive -- there is no reason for an SEO tool to skip them,
and skipping them is how an audit can report a 90/100 page that Google is not
allowed to index.

Only one level of sitemap index is followed: a large store can have hundreds of
child sitemaps, and this runs inside a request.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Optional
from urllib.parse import urljoin, urlparse

from app.core.logger import get_logger

from . import fetcher

logger = get_logger(__name__)

MAX_SITEMAP_URLS_SCANNED = 5000
_LOC_RE = re.compile(r"<loc>\s*([^<\s]+)\s*</loc>", re.IGNORECASE)


@dataclass
class SiteFiles:
    origin: str
    robots_found: bool = False
    robots_url: Optional[str] = None
    robots_status: Optional[int] = None
    blocks_this_page: bool = False
    blocking_rule: Optional[str] = None
    sitemaps_declared: list[str] = field(default_factory=list)
    sitemap_checked: Optional[str] = None
    sitemap_found: bool = False
    sitemap_is_index: bool = False
    sitemap_url_count: int = 0
    contains_this_page: Optional[bool] = None
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "origin": self.origin,
            "robots_found": self.robots_found,
            "robots_url": self.robots_url,
            "robots_status": self.robots_status,
            "blocks_this_page": self.blocks_this_page,
            "blocking_rule": self.blocking_rule,
            "sitemaps_declared": self.sitemaps_declared,
            "sitemap_checked": self.sitemap_checked,
            "sitemap_found": self.sitemap_found,
            "sitemap_is_index": self.sitemap_is_index,
            "sitemap_url_count": self.sitemap_url_count,
            "contains_this_page": self.contains_this_page,
            "notes": self.notes,
        }


def _parse_robots(body: str) -> tuple[list[tuple[str, str]], list[str]]:
    """Return ([(directive, path)], [sitemap urls]) for the groups that apply to
    us: `User-agent: *` and any Googlebot group, since those are the two that
    decide whether this page can be indexed at all."""
    rules: list[tuple[str, str]] = []
    sitemaps: list[str] = []
    applies = False

    for raw in body.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        field_name, _, value = line.partition(":")
        field_name = field_name.strip().lower()
        value = value.strip()

        if field_name == "user-agent":
            applies = value == "*" or value.lower().startswith("googlebot")
        elif field_name == "sitemap" and value:
            sitemaps.append(value)
        elif applies and field_name in ("allow", "disallow"):
            rules.append((field_name, value))

    return rules, sitemaps


def _path_blocked(rules: list[tuple[str, str]], path: str) -> Optional[str]:
    """Standard longest-match resolution: the most specific rule wins, and an
    Allow of equal length beats a Disallow."""
    best: Optional[tuple[int, str, str]] = None
    for directive, value in rules:
        if value == "":
            # `Disallow:` with an empty value means "allow everything".
            continue
        pattern = value.rstrip("*")
        if path.startswith(pattern):
            length = len(pattern)
            if best is None or length > best[0] or (length == best[0] and directive == "allow"):
                best = (length, directive, value)
    if best and best[1] == "disallow":
        return f"Disallow: {best[2]}"
    return None


async def check(page_url: str) -> SiteFiles:
    """Fetch robots.txt for this page's origin, then the sitemap it declares."""
    parts = urlparse(page_url)
    origin = f"{parts.scheme}://{parts.netloc}"
    path = parts.path or "/"
    result = SiteFiles(origin=origin)

    robots_url = urljoin(origin, "/robots.txt")
    result.robots_url = robots_url
    robots = await fetcher.fetch(robots_url)
    result.robots_status = robots.status

    if robots.ok and robots.content.strip():
        result.robots_found = True
        rules, sitemaps = _parse_robots(robots.content)
        result.sitemaps_declared = sitemaps[:10]
        blocking = _path_blocked(rules, path)
        if blocking:
            result.blocks_this_page = True
            result.blocking_rule = blocking
    elif robots.status == 404:
        result.notes.append(
            "No hay robots.txt. No es un error grave (sin él se puede rastrear todo), pero es "
            "el archivo donde se declara el sitemap."
        )
    else:
        result.notes.append(
            f"No se pudo leer robots.txt ({robots.error or f'HTTP {robots.status}'})."
        )

    # The sitemap robots.txt declares, or the conventional location.
    candidate = result.sitemaps_declared[0] if result.sitemaps_declared else urljoin(origin, "/sitemap.xml")
    result.sitemap_checked = candidate
    sitemap = await fetcher.fetch(candidate)

    if sitemap.ok and "<" in sitemap.content:
        result.sitemap_found = True
        body = sitemap.content
        result.sitemap_is_index = "<sitemapindex" in body.lower()
        locs = _LOC_RE.findall(body)[:MAX_SITEMAP_URLS_SCANNED]
        result.sitemap_url_count = len(locs)

        if result.sitemap_is_index:
            result.notes.append(
                f"Es un índice de sitemaps ({len(locs)} sitemaps hijos). Se revisó el primero."
            )
            if locs:
                child = await fetcher.fetch(locs[0])
                if child.ok:
                    child_locs = _LOC_RE.findall(child.content)[:MAX_SITEMAP_URLS_SCANNED]
                    result.sitemap_url_count = len(child_locs)
                    locs = child_locs

        normalized = {loc.rstrip("/") for loc in locs}
        result.contains_this_page = page_url.rstrip("/") in normalized
    else:
        result.notes.append(
            "No se encontró sitemap.xml. Sin sitemap, Google descubre tus páginas sólo si algo "
            "las enlaza; para un catálogo eso deja productos sin indexar."
        )

    return result


def issues_from(files: SiteFiles) -> list[dict[str, str]]:
    """The findings that come out of the two files, in the same shape the page
    analyzer emits so the UI renders them identically."""
    issues: list[dict[str, str]] = []

    if files.blocks_this_page:
        issues.append({
            "severity": "critical",
            "key": "robots_blocks",
            "title": "robots.txt bloquea esta página",
            "detail": f"La regla «{files.blocking_rule}» le prohíbe a Google rastrear esta URL. "
                      "Todo el resto del SEO de esta página es irrelevante mientras siga así.",
            "fix": "Sacá o acotá esa regla en robots.txt para que la URL quede permitida.",
        })

    if not files.sitemap_found:
        issues.append({
            "severity": "warning",
            "key": "no_sitemap",
            "title": "Sin sitemap.xml",
            "detail": "No se encontró un sitemap en robots.txt ni en /sitemap.xml.",
            "fix": "Publicá un sitemap.xml con tus páginas y productos, y declaralo en robots.txt "
                   "con una línea «Sitemap: https://tudominio.com/sitemap.xml».",
        })
    elif files.contains_this_page is False:
        issues.append({
            "severity": "warning",
            "key": "not_in_sitemap",
            "title": "Esta página no está en el sitemap",
            "detail": f"El sitemap tiene {files.sitemap_url_count} URLs y ésta no está entre ellas.",
            "fix": "Agregá esta URL al sitemap para que Google la descubra sin depender de enlaces.",
        })

    if files.robots_found and not files.sitemaps_declared:
        issues.append({
            "severity": "info",
            "key": "sitemap_not_declared",
            "title": "robots.txt no declara el sitemap",
            "detail": "El sitemap existe o podría existir, pero robots.txt no lo anuncia.",
            "fix": "Sumá la línea «Sitemap: https://tudominio.com/sitemap.xml» a robots.txt.",
        })

    return issues
