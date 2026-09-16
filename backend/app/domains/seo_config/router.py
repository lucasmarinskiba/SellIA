"""SEO Config API endpoints."""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.seo_config.service import SEOConfigService, PublicationLinkService
from app.domains.seo_config.models import PublicationLink

router = APIRouter(prefix="/{business_id}/seo-config", tags=["SEO Config"])


# ── Schemas ──
class SEOConfigResponse(BaseModel):
    id: UUID
    business_id: UUID
    global_seo_enabled: bool


class PlatformSEOResponse(BaseModel):
    connection_id: str
    platform_name: str
    status: str
    last_sync: str | None
    seo_enabled: bool


class PlatformSEOListResponse(BaseModel):
    platforms: list[PlatformSEOResponse]
    global_seo_enabled: bool


class PublicationLinkResponse(BaseModel):
    id: UUID
    url: str
    title: str
    platform_source: str
    product_id: UUID | None
    seo_enabled: bool


class CreatePublicationLinkRequest(BaseModel):
    url: str
    title: str
    platform_source: str
    product_id: UUID | None = None


# ── Global SEO Config ──
@router.get("", response_model=SEOConfigResponse)
async def get_seo_config(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get SEO configuration for a business."""
    svc = SEOConfigService(db)
    config = await svc.get_or_create_seo_config(business_id)
    return config


@router.patch("/global-toggle")
async def toggle_global_seo(
    business_id: UUID,
    enabled: bool = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Toggle global SEO on/off for a business."""
    svc = SEOConfigService(db)
    config = await svc.toggle_global_seo(business_id, enabled)
    return {
        "global_seo_enabled": config.global_seo_enabled,
        "message": f"SEO {'activated' if enabled else 'deactivated'} globally",
    }


# ── Platform-specific SEO ──
@router.get("/platforms", response_model=PlatformSEOListResponse)
async def get_platforms_seo_status(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get SEO status for all connected platforms."""
    config_svc = SEOConfigService(db)
    config = await config_svc.get_or_create_seo_config(business_id)
    platforms = await config_svc.list_business_platforms_with_seo(business_id)

    return {
        "platforms": platforms,
        "global_seo_enabled": config.global_seo_enabled,
    }


@router.patch("/platforms/{connection_id}/toggle")
async def toggle_platform_seo(
    business_id: UUID,
    connection_id: UUID,
    enabled: bool = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Toggle SEO on/off for a specific platform."""
    svc = SEOConfigService(db)
    seo_status = await svc.toggle_platform_seo(connection_id, enabled)

    if not seo_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Platform SEO status not found",
        )

    return {
        "connection_id": str(connection_id),
        "seo_enabled": seo_status.seo_enabled,
        "message": f"SEO for {seo_status.platform_name} {'activated' if enabled else 'deactivated'}",
    }


# ── Publication Links ──
@router.get("/publication-links", response_model=list[PublicationLinkResponse])
async def list_publication_links(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all publication links for SEO positioning."""
    svc = PublicationLinkService(db)
    links = await svc.list_business_publication_links(business_id)
    return links


@router.post("/publication-links", response_model=PublicationLinkResponse)
async def create_publication_link(
    business_id: UUID,
    data: CreatePublicationLinkRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a new publication link for SEO positioning."""
    svc = PublicationLinkService(db)
    link = await svc.create_publication_link(
        business_id=business_id,
        url=data.url,
        title=data.title,
        platform_source=data.platform_source,
        product_id=data.product_id,
    )
    return link


@router.patch("/publication-links/{link_id}/toggle")
async def toggle_publication_link_seo(
    business_id: UUID,
    link_id: UUID,
    enabled: bool = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Toggle SEO for a specific publication link."""
    svc = PublicationLinkService(db)
    link = await svc.toggle_publication_link_seo(link_id, enabled)

    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Publication link not found",
        )

    return {
        "link_id": str(link_id),
        "url": link.url,
        "seo_enabled": link.seo_enabled,
        "message": f"SEO for '{link.title}' {'activated' if enabled else 'deactivated'}",
    }


@router.delete("/publication-links/{link_id}")
async def delete_publication_link(
    business_id: UUID,
    link_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a publication link."""
    svc = PublicationLinkService(db)
    deleted = await svc.delete_publication_link(link_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Publication link not found",
        )

    return {"message": "Publication link deleted"}
