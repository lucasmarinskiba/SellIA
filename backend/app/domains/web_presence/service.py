"""Web-presence service: store the account's real links, audit them for real,
and derive the SEO / authority reports the dashboard shows.

The rule every function here follows: a signal is either MEASURED (we fetched
the page and read it) or reported as unverifiable, with the reason. Marketplaces
and social networks frequently answer a server-side fetch with 403 or a login
wall; that is a real, honest outcome ("no se pudo verificar automáticamente")
and never gets rounded up into a pass.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger

from . import analyzer, fetcher
from .models import PLATFORM_KINDS, BusinessLink, LinkKind

logger = get_logger(__name__)

#: Platforms known to block server-side fetches behind a login/bot wall. When
#: one of these answers 401/403/429 we say the check could not be run instead
#: of scoring it as a failure of the user's page.
BOT_WALLED = {"instagram", "facebook", "linkedin", "amazon", "tiktok", "threads", "twitter"}


def _host(url: Optional[str]) -> str:
    if not url:
        return ""
    return (urlparse(url).hostname or "").lower().removeprefix("www.")


def serialize_link(link: BusinessLink) -> dict[str, Any]:
    return {
        "id": str(link.id),
        "platform": link.platform,
        "kind": link.kind.value if isinstance(link.kind, LinkKind) else str(link.kind),
        "url": link.url,
        "label": link.label,
        "is_primary": bool(link.is_primary),
        "last_checked_at": link.last_checked_at.isoformat() if link.last_checked_at else None,
        "http_status": link.http_status,
        "final_url": link.final_url,
        "response_ms": link.response_ms,
        "content_bytes": link.content_bytes,
        "fetch_error": link.fetch_error,
        "seo_score": link.seo_score,
        "audit": link.audit,
    }


async def list_links(db: AsyncSession, user_id: uuid.UUID) -> list[BusinessLink]:
    result = await db.execute(
        select(BusinessLink)
        .where(BusinessLink.user_id == user_id)
        .order_by(BusinessLink.is_primary.desc(), BusinessLink.created_at.asc())
    )
    return list(result.scalars().all())


async def upsert_link(
    db: AsyncSession,
    user_id: uuid.UUID,
    *,
    platform: str,
    url: str,
    label: Optional[str] = None,
    is_primary: bool = False,
    business_id: Optional[uuid.UUID] = None,
) -> BusinessLink:
    """Add or update one real link. The URL is normalized (and rejected if it is
    not a fetchable public http(s) URL) before it is ever stored, so the audit
    job never has to deal with junk."""
    # Both raise UnsafeUrlError -> 400 at the API layer. The host is resolved
    # here too, not only at fetch time: storing a URL that can never be fetched
    # let an internal address (169.254.169.254) reach the generated JSON-LD
    # sameAs the user is told to paste into their own site.
    clean = fetcher.normalize_url(url)
    fetcher.assert_public_host(clean)
    kind, default_label = PLATFORM_KINDS.get(platform, (LinkKind.OTHER, platform))

    existing = await db.execute(
        select(BusinessLink).where(
            BusinessLink.user_id == user_id, BusinessLink.url == clean
        )
    )
    link = existing.scalar_one_or_none()

    if link is None:
        link = BusinessLink(
            user_id=user_id,
            business_id=business_id,
            platform=platform,
            kind=kind,
            url=clean,
            label=label or default_label,
            is_primary=is_primary,
        )
        db.add(link)
    else:
        link.platform = platform
        link.kind = kind
        link.label = label or link.label or default_label
        if is_primary:
            link.is_primary = True

    if is_primary:
        for other in await list_links(db, user_id):
            if other.url != clean:
                other.is_primary = False

    await db.commit()
    await db.refresh(link)
    return link


async def delete_link(db: AsyncSession, user_id: uuid.UUID, link_id: uuid.UUID) -> bool:
    result = await db.execute(
        select(BusinessLink).where(
            BusinessLink.id == link_id, BusinessLink.user_id == user_id
        )
    )
    link = result.scalar_one_or_none()
    if link is None:
        return False
    await db.delete(link)
    await db.commit()
    return True


async def audit_link(db: AsyncSession, link: BusinessLink) -> BusinessLink:
    """Fetch this exact URL and store what the page really contains."""
    result = await fetcher.fetch(link.url)

    link.last_checked_at = datetime.now(timezone.utc)
    link.http_status = result.status
    link.final_url = result.final_url
    link.response_ms = result.elapsed_ms
    link.content_bytes = result.content_bytes
    link.fetch_error = result.error[:300] if result.error else None

    if result.ok and "html" in result.content_type.lower():
        audit = analyzer.analyze(result.content, result.final_url)
        link.audit = audit.as_dict()
        link.seo_score = analyzer.score_page(audit, result.elapsed_ms)
    else:
        link.audit = None
        link.seo_score = None

    await db.commit()
    await db.refresh(link)
    return link


async def audit_all(db: AsyncSession, user_id: uuid.UUID) -> list[BusinessLink]:
    links = await list_links(db, user_id)
    for link in links:
        try:
            await audit_link(db, link)
        except Exception as e:  # noqa: BLE001 -- one bad URL must not sink the batch
            logger.warning("audit_link failed for %s: %s", link.url[:120], str(e)[:200])
    return await list_links(db, user_id)


def _unverifiable(link: BusinessLink) -> Optional[str]:
    """Why this link's page could not be read, if it could not be read."""
    if link.last_checked_at is None:
        return "Todavía no se analizó."
    if link.fetch_error:
        return link.fetch_error
    if link.http_status and link.http_status in (401, 403, 429):
        if link.platform in BOT_WALLED:
            return (
                f"{link.platform} bloquea el análisis automático (HTTP {link.http_status}); "
                "el perfil puede estar perfecto, pero no se puede verificar desde el servidor."
            )
        return f"La página respondió HTTP {link.http_status}."
    if link.http_status and link.http_status >= 400:
        return f"La página respondió HTTP {link.http_status}."
    if link.audit is None:
        return "La respuesta no era HTML analizable."
    return None


async def seo_report(db: AsyncSession, user_id: uuid.UUID) -> dict[str, Any]:
    """Per-account SEO state, built only from pages that were really fetched."""
    links = await list_links(db, user_id)
    pages: list[dict[str, Any]] = []
    scored: list[float] = []
    issue_totals: dict[str, dict[str, Any]] = {}

    for link in links:
        blocked = _unverifiable(link)
        entry = {
            "id": str(link.id),
            "platform": link.platform,
            "kind": link.kind.value if isinstance(link.kind, LinkKind) else str(link.kind),
            "url": link.url,
            "is_primary": bool(link.is_primary),
            "checked_at": link.last_checked_at.isoformat() if link.last_checked_at else None,
            "http_status": link.http_status,
            "response_ms": link.response_ms,
            "score": link.seo_score,
            "unverifiable_reason": blocked,
            "issues": (link.audit or {}).get("issues", []) if link.audit else [],
            "title": (link.audit or {}).get("title") if link.audit else None,
            "word_count": (link.audit or {}).get("word_count") if link.audit else None,
            "json_ld_types": (link.audit or {}).get("json_ld_types", []) if link.audit else [],
        }
        pages.append(entry)
        if link.seo_score is not None:
            scored.append(link.seo_score)
        for issue in entry["issues"]:
            bucket = issue_totals.setdefault(
                issue["key"],
                {"key": issue["key"], "title": issue["title"], "severity": issue["severity"],
                 "fix": issue["fix"], "pages": 0},
            )
            bucket["pages"] += 1

    priorities = sorted(
        issue_totals.values(),
        key=lambda i: (analyzer.SEVERITY_ORDER.get(i["severity"], 9), -i["pages"]),
    )

    return {
        "links_total": len(links),
        "pages_analyzed": len(scored),
        "average_score": round(sum(scored) / len(scored), 1) if scored else None,
        "pages": pages,
        "priorities": priorities[:12],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


async def authority_report(db: AsyncSession, user_id: uuid.UUID) -> dict[str, Any]:
    """Is the account's web presence actually connected to itself?

    Authority is not a vibe: search engines follow links and read sameAs. This
    checks, on the real pages, whether the hub links out to each profile,
    whether each profile links back, and whether the hub declares them as the
    same entity in JSON-LD.
    """
    links = await list_links(db, user_id)
    hub = next((link for link in links if link.is_primary), None)
    if hub is None:
        hub = next((link for link in links if link.kind == LinkKind.WEBSITE), None)

    hub_host = _host(hub.final_url or hub.url) if hub else ""
    hub_audit = (hub.audit or {}) if hub else {}
    hub_outbound = set(hub_audit.get("external_hosts", []))
    hub_same_as_hosts = {_host(u) for u in hub_audit.get("json_ld_same_as", [])}

    profiles: list[dict[str, Any]] = []
    connected = 0
    for link in links:
        if hub is not None and link.id == hub.id:
            continue
        target_host = _host(link.final_url or link.url)
        linked_from_hub = bool(hub_host) and target_host in hub_outbound
        declared_same_as = bool(hub_host) and target_host in hub_same_as_hosts
        blocked = _unverifiable(link)
        links_back = (
            hub_host in set((link.audit or {}).get("external_hosts", []))
            if link.audit and hub_host
            else None
        )
        if linked_from_hub:
            connected += 1
        profiles.append({
            "id": str(link.id),
            "platform": link.platform,
            "kind": link.kind.value if isinstance(link.kind, LinkKind) else str(link.kind),
            "url": link.url,
            "linked_from_hub": linked_from_hub,
            "declared_same_as": declared_same_as,
            "links_back_to_hub": links_back,
            "unverifiable_reason": blocked,
        })

    has_org_schema = any(
        t in ("Organization", "LocalBusiness", "Store", "OnlineStore")
        for t in hub_audit.get("json_ld_types", [])
    )

    checks = [
        {
            "key": "hub",
            "title": "Tenés un sitio propio como centro de tu marca",
            "passed": hub is not None and hub.kind == LinkKind.WEBSITE,
            "detail": (
                f"Hub: {hub.url}" if hub else
                "No hay ningún sitio propio cargado: sin un dominio propio, toda tu autoridad "
                "se la queda la plataforma (Instagram, ML) y no tu marca."
            ),
        },
        {
            "key": "org_schema",
            "title": "Tu sitio se identifica con schema Organization",
            "passed": has_org_schema,
            "detail": (
                "Google puede asociar tu marca como entidad."
                if has_org_schema else
                "Sin Organization/LocalBusiness en JSON-LD, Google no sabe que tu web, tus redes "
                "y tu tienda son el mismo negocio."
            ),
        },
        {
            "key": "same_as",
            "title": "Tu sitio declara sus perfiles con sameAs",
            "passed": bool(hub_same_as_hosts),
            "detail": (
                f"Declara {len(hub_same_as_hosts)} perfil(es) como la misma entidad."
                if hub_same_as_hosts else
                "sameAs es el campo con el que se unifican marca, redes y tienda en un panel de "
                "conocimiento. No está."
            ),
        },
        {
            "key": "outbound",
            "title": "Tu sitio enlaza a tus perfiles y tiendas",
            "passed": connected > 0,
            "detail": f"{connected} de {max(len(profiles), 0)} perfiles enlazados desde el sitio.",
        },
    ]

    passed = sum(1 for c in checks if c["passed"])
    return {
        "hub": serialize_link(hub) if hub else None,
        "profiles": profiles,
        "checks": checks,
        "score": round(passed / len(checks) * 100) if checks else 0,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def build_structured_data(
    *,
    business_name: str,
    site_url: str,
    profile_urls: list[str],
    description: Optional[str] = None,
    city: Optional[str] = None,
    country: Optional[str] = None,
    has_physical_location: bool = False,
) -> dict[str, Any]:
    """The JSON-LD this account should actually paste into its site.

    Generated from the account's REAL name, URL and profiles -- this is the fix
    for the `no_schema` / `same_as` findings above, not a generic template.
    """
    node: dict[str, Any] = {
        "@context": "https://schema.org",
        "@type": "LocalBusiness" if has_physical_location else "Organization",
        "name": business_name,
        "url": site_url,
    }
    if description:
        node["description"] = description
    if profile_urls:
        node["sameAs"] = profile_urls
    if city or country:
        node["address"] = {
            "@type": "PostalAddress",
            **({"addressLocality": city} if city else {}),
            **({"addressCountry": country} if country else {}),
        }
    return node
