"""Web presence API — the account's real links, really audited.

Every route is per-account (get_current_user); there is no unauthenticated
variant, because there is no such thing as "the platform's links".
"""

from __future__ import annotations

import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User

from . import analyzer, fetcher, service
from .models import PLATFORM_KINDS, BusinessLink

router = APIRouter(prefix="/web-presence", tags=["Web Presence"])


class LinkIn(BaseModel):
    platform: str = Field(..., max_length=40)
    url: str = Field(..., max_length=1024)
    label: Optional[str] = Field(None, max_length=200)
    is_primary: bool = False


class UrlIn(BaseModel):
    url: str = Field(..., max_length=1024)


@router.get("/platforms")
async def list_platforms() -> dict[str, Any]:
    """The platform vocabulary the UI should offer (slug, kind, label)."""
    return {
        "platforms": [
            {"platform": slug, "kind": kind.value, "label": label}
            for slug, (kind, label) in PLATFORM_KINDS.items()
        ]
    }


@router.get("/links")
async def get_links(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    links = await service.list_links(db, user.id)
    return {"links": [service.serialize_link(link) for link in links]}


@router.post("/links")
async def add_link(
    payload: LinkIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    try:
        link = await service.upsert_link(
            db,
            user.id,
            platform=payload.platform,
            url=payload.url,
            label=payload.label,
            is_primary=payload.is_primary,
        )
    except fetcher.UnsafeUrlError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return service.serialize_link(link)


@router.delete("/links/{link_id}")
async def remove_link(
    link_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, bool]:
    deleted = await service.delete_link(db, user.id, link_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Link no encontrado")
    return {"deleted": True}


@router.post("/links/{link_id}/audit")
async def audit_one(
    link_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    result = await db.execute(
        select(BusinessLink).where(
            BusinessLink.id == link_id, BusinessLink.user_id == user.id
        )
    )
    link = result.scalar_one_or_none()
    if link is None:
        raise HTTPException(status_code=404, detail="Link no encontrado")
    return service.serialize_link(await service.audit_link(db, link))


@router.post("/audit-all")
async def audit_everything(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    links = await service.audit_all(db, user.id)
    return {"links": [service.serialize_link(link) for link in links]}


@router.post("/analyze-url")
async def analyze_any_url(payload: UrlIn, _: User = Depends(get_current_user)) -> dict[str, Any]:
    """One-off audit of any public URL (a competitor's page, a listing you are
    about to publish). Not stored -- use POST /links to keep it."""
    result = await fetcher.fetch(payload.url)
    if not result.ok:
        return {
            "ok": False,
            "url": result.url,
            "http_status": result.status,
            "error": result.error or f"HTTP {result.status}",
            "response_ms": result.elapsed_ms,
        }
    audit = analyzer.analyze(result.content, result.final_url)
    return {
        "ok": True,
        "url": result.url,
        "final_url": result.final_url,
        "http_status": result.status,
        "response_ms": result.elapsed_ms,
        "content_bytes": result.content_bytes,
        "score": analyzer.score_page(audit, result.elapsed_ms),
        "audit": audit.as_dict(),
    }


@router.post("/compare")
async def compare_with_competitor(
    payload: UrlIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Your main page against a competitor's, on the signals that can actually
    be read from both pages -- plus which topics their page covers that yours
    never mentions. No estimated 'domain authority' anywhere: that number needs
    a paid backlink index (see docs/INTEGRACIONES.md)."""
    links = await service.list_links(db, user.id)
    mine = next((link for link in links if link.is_primary and link.audit), None) or next(
        (link for link in links if link.audit), None
    )
    if mine is None:
        raise HTTPException(
            status_code=400,
            detail="Primero cargá y analizá al menos una página tuya para poder compararla.",
        )

    result = await fetcher.fetch(payload.url)
    if not result.ok:
        return {
            "ok": False,
            "error": result.error or f"HTTP {result.status}",
            "url": result.url,
        }

    theirs = analyzer.analyze(result.content, result.final_url)
    theirs_dict = theirs.as_dict()
    mine_dict = mine.audit or {}

    def row(label: str, mine_value: Any, their_value: Any, higher_is_better: bool = True) -> dict[str, Any]:
        return {
            "label": label,
            "mine": mine_value,
            "theirs": their_value,
            "higher_is_better": higher_is_better,
        }

    my_terms = {t["term"] for t in (mine_dict.get("terms") or {}).get("top_terms", [])}
    their_terms = [t["term"] for t in (theirs_dict.get("terms") or {}).get("top_terms", [])]

    return {
        "ok": True,
        "mine": {"url": mine.url, "score": mine.seo_score, "title": mine_dict.get("title")},
        "theirs": {
            "url": result.final_url,
            "score": analyzer.score_page(theirs, result.elapsed_ms),
            "title": theirs_dict.get("title"),
        },
        "rows": [
            row("Palabras de contenido", mine_dict.get("word_count"), theirs_dict.get("word_count")),
            row("Tipos de datos estructurados",
                len(mine_dict.get("json_ld_types", [])), len(theirs_dict.get("json_ld_types", []))),
            row("Enlaces internos", mine_dict.get("internal_links"), theirs_dict.get("internal_links")),
            row("Imágenes sin alt",
                mine_dict.get("images_without_alt"), theirs_dict.get("images_without_alt"), False),
            row("Tiempo de respuesta (ms)", mine.response_ms, result.elapsed_ms, False),
            row("Hallazgos abiertos",
                len(mine_dict.get("issues", [])), len(theirs_dict.get("issues", [])), False),
        ],
        "topics_they_cover": [t for t in their_terms if t not in my_terms][:10],
        "their_schema": theirs_dict.get("json_ld_types", []),
    }


@router.get("/seo-report")
async def get_seo_report(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    return await service.seo_report(db, user.id)


@router.get("/authority-report")
async def get_authority_report(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    return await service.authority_report(db, user.id)


@router.get("/structured-data")
async def get_structured_data(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """The exact JSON-LD this account should paste into its site, built from its
    own real business data and its own real profile URLs."""
    links = await service.list_links(db, user.id)
    hub = next((link for link in links if link.is_primary), None) or next(
        (link for link in links if link.kind.value == "website"), None
    )
    if hub is None:
        return {
            "available": False,
            "reason": (
                "Cargá primero tu sitio web (o tu tienda principal) para poder generar "
                "los datos estructurados de tu marca."
            ),
        }

    business_name = user.full_name or (user.email.split("@")[0] if user.email else "Mi negocio")
    city = country = description = None
    has_physical = False
    try:
        from app.domains.business_context.models import BusinessContext

        ctx_result = await db.execute(
            select(BusinessContext).where(BusinessContext.user_id == user.id).limit(1)
        )
        ctx = ctx_result.scalar_one_or_none()
        if ctx is not None:
            description = ctx.value_proposition or ctx.industry
            city = ctx.city
            country = ctx.country
            has_physical = bool(ctx.has_physical_location)
    except Exception:  # noqa: BLE001 -- schema is still generated without context
        pass

    node = service.build_structured_data(
        business_name=business_name,
        site_url=hub.final_url or hub.url,
        profile_urls=[link.url for link in links if link.id != hub.id],
        description=description,
        city=city,
        country=country,
        has_physical_location=has_physical,
    )
    return {"available": True, "json_ld": node}
