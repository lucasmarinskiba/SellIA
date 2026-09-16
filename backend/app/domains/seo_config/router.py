"""SEO Config API endpoints."""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.seo_config.service import SEOConfigService, PublicationLinkService
from app.domains.seo_config.fomo_generator import PublicationFOMOGenerator
from app.domains.seo_config.platform_sync_service import PlatformListingSyncService
from app.domains.seo_config.models import PublicationLink, PublicationLinkFOMO, PlatformSyncLog

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


class PublicationLinkFOMOResponse(BaseModel):
    id: UUID
    link_id: UUID
    urgency_trigger: str | None
    social_proof_element: str | None
    scarcity_message: str | None
    call_to_action: str
    generated_copy: str
    fomo_score: float


class FOOMGenerationResponse(BaseModel):
    business_id: str
    links_processed: int
    fomo_generated: int
    failed: int


class PlatformSyncResponse(BaseModel):
    business_id: str
    links_processed: int
    synced: int
    failed: int
    skipped: int


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


# ── FOMO Copy Generation ──
@router.post("/{business_id}/generate-fomo-all", response_model=FOOMGenerationResponse)
async def generate_fomo_all(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate FOMO copy for all active publication links."""
    generator = PublicationFOMOGenerator(db)
    result = await generator.generate_fomo_for_business(business_id)
    return result


@router.post("/publication-links/{link_id}/generate-fomo", response_model=PublicationLinkFOMOResponse)
async def generate_fomo_for_link(
    business_id: UUID,
    link_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate FOMO copy for a specific publication link."""
    svc = PublicationLinkService(db)
    link = await svc.get_publication_link(link_id)

    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Publication link not found",
        )

    generator = PublicationFOMOGenerator(db)
    fomo_entry = await generator.generate_fomo_for_link(business_id, link)

    if not fomo_entry:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate FOMO copy. Check logs for details.",
        )

    return fomo_entry


@router.get("/publication-links/{link_id}/fomo", response_model=PublicationLinkFOMOResponse | None)
async def get_link_fomo(
    business_id: UUID,
    link_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get latest FOMO copy for a publication link."""
    generator = PublicationFOMOGenerator(db)
    fomo_entry = await generator.get_latest_fomo(link_id)
    return fomo_entry


# ── Platform Sync ──
@router.post("/{business_id}/sync-all", response_model=PlatformSyncResponse)
async def sync_all_links(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Sync FOMO copy for all active publication links to their platforms."""
    sync_service = PlatformListingSyncService(db)
    result = await sync_service.sync_all_links(business_id)
    return result


@router.post("/publication-links/{link_id}/sync")
async def sync_link(
    business_id: UUID,
    link_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Sync FOMO copy for a specific link to its platform."""
    svc = PublicationLinkService(db)
    link = await svc.get_publication_link(link_id)

    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Publication link not found",
        )

    # Get latest FOMO
    fomo_result = await db.execute(
        select(PublicationLinkFOMO)
        .where(PublicationLinkFOMO.link_id == link_id)
        .order_by(PublicationLinkFOMO.created_at.desc())
        .limit(1)
    )
    fomo = fomo_result.scalar_one_or_none()

    if not fomo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No FOMO copy generated yet. Generate FOMO first.",
        )

    sync_service = PlatformListingSyncService(db)
    log = await sync_service.sync_fomo_to_listing(business_id, link, fomo)

    return {
        "log_id": str(log.id),
        "status": log.status,
        "error_message": log.error_message,
        "platform": log.platform_name,
        "external_listing_id": log.external_listing_id,
    }


@router.get("/{business_id}/sync-history")
async def get_sync_history(
    business_id: UUID,
    limit: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get sync history for a business."""
    result = await db.execute(
        select(PlatformSyncLog)
        .where(PlatformSyncLog.business_id == business_id)
        .order_by(PlatformSyncLog.created_at.desc())
        .limit(limit)
    )
    logs = result.scalars().all()

    return [
        {
            "id": str(log.id),
            "link_id": str(log.link_id),
            "platform": log.platform_name,
            "status": log.status,
            "external_listing_id": log.external_listing_id,
            "error_message": log.error_message,
            "synced_at": log.synced_at.isoformat() if log.synced_at else None,
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]
