"""SEO Config API endpoints."""

from uuid import UUID
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.logger import get_logger
from app.domains.users.models import User
from app.domains.businesses.models import Business
from app.domains.seo_config.service import SEOConfigService, PublicationLinkService
from app.domains.seo_config.fomo_generator import PublicationFOMOGenerator
from app.domains.seo_config.platform_sync_service import PlatformListingSyncService
from app.domains.seo_config.bulk_import import BulkListingImporter
from app.domains.seo_config.models import PublicationLink, PublicationLinkFOMO, PlatformSyncLog, PlatformSEOStatus
from app.domains.seo_config.platform_analytics_service import PlatformAnalyticsService
from app.domains.seo_config.analytics_models import PublicationLinkMetrics, PublicationLinkPerformanceSummary
from app.domains.seo_config.fomo_service import FOMAConversionService
from app.domains.seo_config.fomo_models import ConversionEvent
from app.domains.seo_config.fomo_abtest_service import FOMABTestService
from app.domains.seo_config.fomo_decay_service import FOMADecayService
from app.domains.seo_config.fomo_predictive import FOMAPredictor
from app.domains.seo_config.fomo_crossplatform import FOMAPatternSynthesizer
from app.domains.seo_config.fomo_feedback_loop import FOMAFeedbackLoop
from app.domains.seo_config.webhook_service import WebhookService
from app.domains.seo_config.mercadolibre_webhook_service import (
    NotificationRejected,
    authenticate_channel,
    parse_notification,
    run_order_notification,
)
from app.domains.seo_config.webhook_models import ConversionWebhookPayload, WebhookEventResponse
from app.domains.seo_config.fomo_auto_rotation import FOMAAutoRotator
from app.domains.seo_config.fomo_language_generator import FOMALanguageGenerator
from app.domains.seo_config.platform_algorithm_knowledge import (
    GUIDANCE_ONLY, MEASURED, PROFILES, canonical_platform, coverage_for, get_profile, profile_to_dict,
)
from app.domains.seo_config.positioning_score_service import PositioningScoreService, recommendation_payload
from app.domains.seo_config.store_positioning_service import StorePositioningScoreService

logger = get_logger(__name__)

async def verify_business_access(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Business:
    """Every endpoint on `router` below takes a `business_id` straight from the
    URL with no other proof it belongs to the caller — this was a plain IDOR:
    any logged-in user could read or write any other business's SEO config,
    publication links, FOMO copy, conversions and positioning data just by
    changing the id in the path. Applied once at router level (not per-route)
    so no endpoint can be added later without it."""
    business = await db.get(Business, business_id)
    if not business:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")
    if business.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tenés acceso a este negocio")
    return business


router = APIRouter(
    prefix="/{business_id}/seo-config",
    tags=["SEO Config"],
    dependencies=[Depends(verify_business_access)],
)

# Mercado Libre calls this one directly with its own channel token, never a user
# session — it must stay outside the ownership check above (there's no
# current_user to check against). Same path prefix, mounted separately in
# main.py so it's never bundled with the authenticated routes.
public_router = APIRouter(prefix="/{business_id}/seo-config", tags=["SEO Config Webhooks"])


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


class BulkImportListingRequest(BaseModel):
    platform_source: str
    listings: list[dict]  # [{url, title, product_id (opt)}]


class BulkImportResponse(BaseModel):
    imported: int
    fomo_generated: int
    failed: int


class PublicationLinkMetricsResponse(BaseModel):
    id: UUID
    link_id: UUID
    metric_date: str
    platform_name: str
    impressions: int
    clicks: int
    conversions: int
    ctr: float
    conversion_rate: float
    revenue: float


class PerformanceSummaryResponse(BaseModel):
    id: UUID
    link_id: UUID
    period_start: str
    period_end: str
    total_impressions: int
    total_clicks: int
    total_conversions: int
    total_revenue: float
    avg_ctr: float
    avg_conversion_rate: float


class ConversionEventResponse(BaseModel):
    id: UUID
    link_id: UUID
    platform_name: str
    conversion_type: str
    conversion_value: float
    created_at: str


class UrgencyMetricsResponse(BaseModel):
    triggers: list[dict]


class FOMAPreviewResponse(BaseModel):
    link: dict
    original: dict
    with_fomo: dict


class CreateABTestRequest(BaseModel):
    link_id: UUID
    variant_a_id: UUID
    variant_b_id: UUID
    variant_c_id: UUID | None = None
    min_conversions: int = 100


class ABTestMetricsResponse(BaseModel):
    test_id: str
    status: str
    min_conversions: int
    total_conversions: int
    variant_a: dict
    variant_b: dict
    variant_c: dict | None
    winner_id: str | None
    winner_announced_at: str | None


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
    config = await svc.toggle_global_seo(
        business_id, enabled,
        user_id=current_user.id, user_email=getattr(current_user, "email", None),
    )
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
@router.post("/generate-fomo-all", response_model=FOOMGenerationResponse)
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
@router.post("/sync-all", response_model=PlatformSyncResponse)
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


@router.get("/sync-history")
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


# ── Bulk Operations ──
@router.post("/bulk-import", response_model=BulkImportResponse)
async def bulk_import_listings(
    business_id: UUID,
    data: BulkImportListingRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Bulk import listings from a platform.

    Creates PublicationLink for each + auto-generates FOMO copy.
    """
    importer = BulkListingImporter(db)
    result = await importer.import_listings_from_platform(
        business_id,
        data.listings,
        data.platform_source,
    )
    return result


# ── Analytics ──
@router.post("/analytics/refresh")
async def refresh_analytics(
    business_id: UUID,
    link_id: UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Refresh analytics metrics from platforms.

    If link_id provided: fetch metrics for one link.
    If not: fetch for all links.
    """
    analytics_svc = PlatformAnalyticsService(db)

    if link_id:
        # Single link
        svc = PublicationLinkService(db)
        link = await svc.get_publication_link(link_id)
        if not link:
            raise HTTPException(status_code=404, detail="Link not found")

        metrics = await analytics_svc.fetch_and_store_metrics(
            business_id,
            link,
            link.url.split("/")[-1],
            link.connection_id,
        )
        return {
            "refreshed": 1 if metrics else 0,
            "link_id": str(link_id),
            "status": "success" if metrics else "no_data",
        }
    else:
        # All links
        svc = PublicationLinkService(db)
        links = await svc.list_business_publication_links(business_id)

        refreshed = 0
        for link in links:
            metrics = await analytics_svc.fetch_and_store_metrics(
                business_id,
                link,
                link.url.split("/")[-1],
                link.connection_id,
            )
            if metrics:
                refreshed += 1

        return {
            "refreshed": refreshed,
            "total": len(links),
            "status": "success",
        }


@router.get("/analytics/{link_id}/daily", response_model=list[PublicationLinkMetricsResponse])
async def get_link_daily_metrics(
    business_id: UUID,
    link_id: UUID,
    days: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get daily metrics for a publication link (last N days)."""
    from datetime import date, timedelta

    start_date = date.today() - timedelta(days=days)
    end_date = date.today()

    result = await db.execute(
        select(PublicationLinkMetrics)
        .where(
            PublicationLinkMetrics.link_id == link_id,
            PublicationLinkMetrics.business_id == business_id,
            PublicationLinkMetrics.metric_date >= start_date,
            PublicationLinkMetrics.metric_date <= end_date,
        )
        .order_by(PublicationLinkMetrics.metric_date.desc())
    )
    metrics = result.scalars().all()

    return [
        {
            "id": m.id,
            "link_id": m.link_id,
            "metric_date": m.metric_date.isoformat(),
            "platform_name": m.platform_name,
            "impressions": m.impressions,
            "clicks": m.clicks,
            "conversions": m.conversions,
            "ctr": round(m.ctr, 2),
            "conversion_rate": round(m.conversion_rate, 2),
            "revenue": round(m.revenue, 2),
        }
        for m in metrics
    ]


@router.get("/analytics/{link_id}/summary", response_model=list[PerformanceSummaryResponse])
async def get_link_performance_summary(
    business_id: UUID,
    link_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get aggregated performance summaries for a publication link."""
    result = await db.execute(
        select(PublicationLinkPerformanceSummary)
        .where(
            PublicationLinkPerformanceSummary.link_id == link_id,
            PublicationLinkPerformanceSummary.business_id == business_id,
        )
        .order_by(PublicationLinkPerformanceSummary.period_end.desc())
    )
    summaries = result.scalars().all()

    return [
        {
            "id": s.id,
            "link_id": s.link_id,
            "period_start": s.period_start.isoformat(),
            "period_end": s.period_end.isoformat(),
            "total_impressions": s.total_impressions,
            "total_clicks": s.total_clicks,
            "total_conversions": s.total_conversions,
            "total_revenue": round(s.total_revenue, 2),
            "avg_ctr": round(s.avg_ctr, 2),
            "avg_conversion_rate": round(s.avg_conversion_rate, 2),
        }
        for s in summaries
    ]


@router.get("/analytics", response_model=dict)
async def get_business_analytics_overview(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get analytics overview for all publication links (today's metrics)."""
    from datetime import date

    result = await db.execute(
        select(PublicationLinkMetrics)
        .where(
            PublicationLinkMetrics.business_id == business_id,
            PublicationLinkMetrics.metric_date == date.today(),
        )
    )
    today_metrics = result.scalars().all()

    total_impressions = sum(m.impressions for m in today_metrics)
    total_clicks = sum(m.clicks for m in today_metrics)
    total_conversions = sum(m.conversions for m in today_metrics)
    total_revenue = sum(m.revenue for m in today_metrics)

    avg_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
    avg_conv_rate = (total_conversions / total_clicks * 100) if total_clicks > 0 else 0

    return {
        "business_id": str(business_id),
        "metric_date": date.today().isoformat(),
        "total_impressions": total_impressions,
        "total_clicks": total_clicks,
        "total_conversions": total_conversions,
        "total_revenue": round(total_revenue, 2),
        "avg_ctr": round(avg_ctr, 2),
        "avg_conversion_rate": round(avg_conv_rate, 2),
        "links_tracked": len(today_metrics),
    }


# ── FOMO Phase 1: Real-time Ticker + Preview + Metrics ──

@router.post("/conversions/track")
async def track_conversion(
    business_id: UUID,
    link_id: UUID = Query(...),
    platform_name: str = Query(...),
    conversion_type: str = Query("purchase"),
    conversion_value: float = Query(0.0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Track a conversion event from platform webhook."""
    link = await db.get(PublicationLink, link_id)
    if not link or link.business_id != business_id:
        raise HTTPException(status_code=404, detail="Link no encontrado para este negocio")

    svc = FOMAConversionService(db)
    event = await svc.log_conversion(
        business_id=business_id,
        link_id=link_id,
        platform_name=platform_name,
        conversion_type=conversion_type,
        conversion_value=conversion_value,
    )
    if event is None:
        raise HTTPException(status_code=409, detail="Conversión duplicada")

    return {
        "id": str(event.id),
        "status": "tracked",
        "created_at": event.created_at.isoformat(),
    }


@router.get("/conversions/recent", response_model=list[ConversionEventResponse])
async def get_recent_conversions(
    business_id: UUID,
    limit: int = Query(10, ge=1, le=50),
    hours_back: int = Query(24, ge=1, le=168),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get recent conversions for real-time ticker."""
    svc = FOMAConversionService(db)
    conversions = await svc.get_recent_conversions(
        business_id,
        limit=limit,
        hours_back=hours_back,
    )

    return [
        {
            "id": c.id,
            "link_id": c.link_id,
            "platform_name": c.platform_name,
            "conversion_type": c.conversion_type,
            "conversion_value": c.conversion_value,
            "created_at": c.created_at.isoformat(),
        }
        for c in conversions
    ]


@router.get("/analytics/urgency-metrics", response_model=UrgencyMetricsResponse)
async def get_urgency_metrics(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get CTR breakdown by urgency trigger type."""
    svc = FOMAConversionService(db)
    metrics = await svc.get_urgency_metrics(business_id)
    return metrics


@router.get("/publication-links/{link_id}/preview", response_model=FOMAPreviewResponse)
async def get_fomo_preview(
    business_id: UUID,
    link_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get FOMO preview: original vs FOMO copy side-by-side."""
    svc = FOMAConversionService(db)
    preview = await svc.get_fomo_preview(link_id)

    if not preview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link not found",
        )

    return preview


# ── FOMO Phase 2: A/B Testing ──

@router.post("/fomo-ab-tests", response_model=dict)
async def create_ab_test(
    business_id: UUID,
    data: CreateABTestRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create A/B test for FOMO variants."""
    svc = FOMABTestService(db)
    try:
        test = await svc.create_ab_test(
            business_id=business_id,
            link_id=data.link_id,
            variant_a_id=data.variant_a_id,
            variant_b_id=data.variant_b_id,
            variant_c_id=data.variant_c_id,
            min_conversions=data.min_conversions,
        )
        return {
            "id": str(test.id),
            "status": test.status,
            "link_id": str(test.link_id),
            "created_at": test.created_at.isoformat(),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/fomo-ab-tests/{test_id}", response_model=ABTestMetricsResponse)
async def get_ab_test_metrics(
    business_id: UUID,
    test_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get A/B test metrics and status."""
    svc = FOMABTestService(db)
    metrics = await svc.get_test_metrics(test_id)

    if not metrics:
        raise HTTPException(status_code=404, detail="Test not found")

    return metrics


@router.post("/fomo-ab-tests/{test_id}/apply-winner", response_model=dict)
async def apply_ab_test_winner(
    business_id: UUID,
    test_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Apply winning variant to publication link."""
    svc = FOMABTestService(db)

    # Check and announce winner if not done yet
    test = await svc.check_and_announce_winner(test_id)
    if not test or not test.winner_variant_id:
        raise HTTPException(
            status_code=400,
            detail="Test not completed or no winner yet. Minimum conversions not reached.",
        )

    # Apply winner
    link = await svc.apply_winner_to_link(test_id)
    if not link:
        raise HTTPException(status_code=500, detail="Failed to apply winner")

    return {
        "test_id": str(test_id),
        "winner_variant_id": str(test.winner_variant_id),
        "link_id": str(link.id),
        "status": "applied",
    }


@router.get("/fomo-ab-tests/running", response_model=list[dict])
async def list_running_tests(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all running A/B tests for business."""
    svc = FOMABTestService(db)
    tests = await svc.list_running_tests(business_id)

    result = []
    for test in tests:
        metrics = await svc.get_test_metrics(test.id)
        result.append(metrics)

    return result


# ── FOMO Phase 3: Smart Rotation + Decay Detection ──

@router.get("/fomo-decay/detect", response_model=list[dict])
async def detect_fomo_decay(
    business_id: UUID,
    decay_threshold: float = Query(30.0, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Detect FOMO copy decay (CTR drop > threshold)."""
    svc = FOMADecayService(db)
    decayed_links = await svc.get_links_with_decay(
        business_id,
        decay_threshold_pct=decay_threshold,
    )
    return decayed_links


@router.get("/fomo-decay/history", response_model=list[dict])
async def get_decay_history(
    business_id: UUID,
    limit: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get decay detection history."""
    svc = FOMADecayService(db)
    logs = await svc.get_decay_history(business_id, limit=limit)

    return [
        {
            "id": str(log.id),
            "link_id": str(log.link_id),
            "baseline_ctr": log.previous_ctr,
            "current_ctr": log.current_ctr,
            "decay_pct": log.decay_percentage,
            "action": log.action,
            "detected_at": log.created_at.isoformat(),
        }
        for log in logs
    ]


# ── FOMO Phase 4: Predictive Scoring ──

@router.get("/fomo-predictions/{link_id}/{fomo_id}", response_model=dict)
async def predict_fomo_conversion(
    business_id: UUID,
    link_id: UUID,
    fomo_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Predict conversion probability for FOMO copy.

    Returns: {"probability": 0-1, "confidence": 0-1, "reasoning": str}
    """
    predictor = FOMAPredictor(db)
    prediction = await predictor.predict_conversion_probability(link_id, fomo_id)

    return {
        "fomo_id": str(fomo_id),
        "link_id": str(link_id),
        **prediction,
    }


@router.get("/fomo-score/{fomo_id}", response_model=dict)
async def get_fomo_effectiveness_score(
    business_id: UUID,
    fomo_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get FOMO copy effectiveness score (0-100).

    Based on: urgency, social proof, scarcity clarity, CTA strength.
    """
    fomo_result = await db.execute(
        select(PublicationLinkFOMO).where(PublicationLinkFOMO.id == fomo_id)
    )
    fomo = fomo_result.scalar_one_or_none()

    if not fomo:
        raise HTTPException(status_code=404, detail="FOMO not found")

    predictor = FOMAPredictor(db)
    score_result = await predictor.compute_fomo_score(fomo)

    return {
        "fomo_id": str(fomo_id),
        **score_result,
    }


@router.get("/fomo-credibility/{fomo_id}", response_model=dict)
async def assess_fomo_credibility(
    business_id: UUID,
    fomo_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Assess if FOMO copy sounds credible or manipulative.

    Returns: {"credibility_score": 0-100, "rating": "trustworthy|borderline|suspicious", "red_flags": []}
    """
    fomo_result = await db.execute(
        select(PublicationLinkFOMO).where(PublicationLinkFOMO.id == fomo_id)
    )
    fomo = fomo_result.scalar_one_or_none()

    if not fomo:
        raise HTTPException(status_code=404, detail="FOMO not found")

    predictor = FOMAPredictor(db)
    credibility = await predictor.get_credibility_assessment(fomo)

    return {
        "fomo_id": str(fomo_id),
        **credibility,
    }


# ── FOMO Phase 5: Cross-Platform Synthesis ──

@router.get("/fomo-patterns/by-platform", response_model=dict)
async def get_trigger_performance(
    business_id: UUID,
    days: int = Query(30, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get avg CTR by urgency trigger per platform."""
    synthesizer = FOMAPatternSynthesizer(db)
    patterns = await synthesizer.get_trigger_performance_by_platform(business_id, days)

    return {
        "business_id": str(business_id),
        "period_days": days,
        "patterns": patterns,
    }


@router.get("/fomo-patterns/best-triggers", response_model=dict)
async def get_best_triggers(
    business_id: UUID,
    days: int = Query(30, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get best-performing trigger per platform."""
    synthesizer = FOMAPatternSynthesizer(db)
    best = await synthesizer.find_best_trigger_per_platform(business_id, days)

    return {
        "business_id": str(business_id),
        "period_days": days,
        "best_triggers": best,
    }


@router.get("/fomo-patterns/recommendations", response_model=list[dict])
async def get_cross_platform_recommendations(
    business_id: UUID,
    days: int = Query(30, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get recommendations to apply winning patterns across platforms."""
    synthesizer = FOMAPatternSynthesizer(db)
    recommendations = await synthesizer.get_cross_platform_recommendations(business_id, days)

    return recommendations


@router.get("/fomo-patterns/trigger-streak/{trigger}", response_model=dict)
async def get_trigger_streak(
    business_id: UUID,
    trigger: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get how well a trigger performs across all platforms."""
    synthesizer = FOMAPatternSynthesizer(db)
    streak = await synthesizer.get_trigger_winning_streak(business_id, trigger)

    return streak


# ── FOMO Phase 6: Closed-Loop Feedback ──

@router.get("/fomo-learning/prediction-accuracy", response_model=dict)
async def get_prediction_accuracy(
    business_id: UUID,
    days: int = Query(30, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get prediction accuracy (predicted vs actual conversions)."""
    feedback_loop = FOMAFeedbackLoop(db)
    accuracy = await feedback_loop.get_prediction_accuracy(business_id, days)

    return {
        "business_id": str(business_id),
        **accuracy,
    }


@router.get("/fomo-learning/velocity", response_model=dict)
async def get_learning_velocity(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get system learning velocity (how fast is it improving)."""
    feedback_loop = FOMAFeedbackLoop(db)
    velocity = await feedback_loop.get_learning_velocity(business_id)

    return {
        "business_id": str(business_id),
        **velocity,
    }


@router.get("/fomo-learning/link-trend/{link_id}", response_model=dict)
async def get_link_effectiveness_trend(
    business_id: UUID,
    link_id: UUID,
    days: int = Query(30, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get FOMO effectiveness trend for a specific link."""
    feedback_loop = FOMAFeedbackLoop(db)
    trend = await feedback_loop.get_fomo_effectiveness_trend(link_id, days)

    return trend


# ── Webhooks: Real-time Conversion Streaming ──

@router.post("/webhooks/conversion", response_model=WebhookEventResponse)
async def ingest_conversion_webhook(
    business_id: UUID,
    payload: ConversionWebhookPayload,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ingest conversion event from any platform."""
    webhook_service = WebhookService(db)
    ip_address = request.client.host if request.client else None

    result = await webhook_service.ingest_conversion(
        business_id=business_id,
        platform=payload.platform,
        payload=payload,
        ip_address=ip_address,
    )

    return result


@public_router.post("/webhooks/mercado-libre", response_model=dict)
async def ingest_mercado_libre_webhook(
    business_id: UUID,
    request: Request,
    background_tasks: BackgroundTasks,
    token: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Mercado Libre order notifications (orders_v2) -> FOMO conversions.

    Register this URL as the notification callback with the Mercado Libre
    channel's webhook token: `...?token=<channel.webhook_token>`. Requests are
    authenticated by that token (bound to this business), then each order is
    confirmed against Mercado Libre's API before anything is recorded — see
    mercadolibre_webhook_service.py for the reasoning. The heavy part runs in
    the background so the 200 goes back to Mercado Libre immediately.
    """
    channel = await authenticate_channel(db, business_id, token)
    if not channel:
        logger.warning(f"ML webhook rejected for business {business_id}: invalid or missing token")
        raise HTTPException(status_code=401, detail="Token de webhook inválido")

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Payload inválido")

    try:
        notification = parse_notification(payload, channel)
    except NotificationRejected as e:
        logger.warning(f"ML webhook rejected for business {business_id}: {e.reason}")
        raise HTTPException(status_code=e.status_code, detail=e.reason)

    if notification is None:
        return {"received": True, "ignored": True}

    background_tasks.add_task(run_order_notification, channel.id, notification.order_id)
    return {"received": True}


@router.get("/webhooks/events/stream")
async def stream_fomo_events(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Server-Sent Events stream for real-time FOMO updates."""
    webhook_service = WebhookService(db)

    async def event_generator():
        async for event in webhook_service.subscribe(business_id):
            yield event

    return StreamingResponse(
        event_generator(),
        media_type='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive',
        },
    )


# ── Smart Auto-Rotation ──

@router.post("/fomo-auto-rotation/trigger", response_model=dict)
async def trigger_auto_rotation(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Manually trigger smart auto-rotation (regenerate + A/B test decayed links)."""
    rotator = FOMAAutoRotator(db)
    result = await rotator.auto_rotate_on_decay(business_id)

    return {
        'business_id': str(business_id),
        'rotated': result.get('rotated'),
        'links': result.get('links'),
    }


@router.get("/fomo-auto-rotation/history", response_model=list[dict])
async def get_rotation_history(
    business_id: UUID,
    days: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get recent auto-rotation history."""
    rotator = FOMAAutoRotator(db)
    history = await rotator.get_rotation_history(business_id, days)

    return history


# ── Multi-Language FOMO ──

@router.post("/fomo-multilingual/generate", response_model=dict)
async def generate_multilingual_fomo(
    business_id: UUID,
    link_id: UUID = Query(...),
    platform: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate FOMO copy in all supported languages (ES/EN/PT)."""
    lang_gen = FOMALanguageGenerator(db)
    result = await lang_gen.generate_multilingual(business_id, link_id, platform)

    return {
        'business_id': str(business_id),
        'link_id': str(link_id),
        'platform': platform,
        'languages': result,
    }


@router.post("/fomo-multilingual/generate-single", response_model=dict)
async def generate_fomo_single_language(
    business_id: UUID,
    link_id: UUID = Query(...),
    platform: str = Query(...),
    language: str = Query('es', regex='^(es|en|pt)$'),
    urgency: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate FOMO copy for a specific language."""
    lang_gen = FOMALanguageGenerator(db)
    result = await lang_gen.generate_for_language(
        business_id=business_id,
        link_id=link_id,
        platform=platform,
        language=language,
        urgency=urgency,
    )

    return result


@router.get("/fomo-multilingual/comparison", response_model=dict)
async def get_language_comparison(
    business_id: UUID,
    link_id: UUID = Query(...),
    platform: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get FOMO copy comparison across all languages for a link."""
    lang_gen = FOMALanguageGenerator(db)
    comparison = await lang_gen.get_language_comparison(business_id, link_id, platform)

    return comparison


@router.get("/fomo-multilingual/supported-languages", response_model=dict)
async def get_supported_languages(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get list of supported languages for FOMO generation."""
    return {
        'supported_languages': FOMALanguageGenerator.SUPPORTED_LANGUAGES,
        'language_names': FOMALanguageGenerator.LANGUAGE_NAMES,
    }


# ── Platform-Algorithm Positioning Score ──

@router.post("/publication-links/{link_id}/positioning/compute", response_model=dict)
async def compute_positioning_score(
    business_id: UUID,
    link_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Compute a fresh platform-algorithm-aware positioning score for one link."""
    result = await db.execute(
        select(PublicationLink).where(
            PublicationLink.id == link_id, PublicationLink.business_id == business_id
        )
    )
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(status_code=404, detail="Publication link not found")

    service = PositioningScoreService(db)
    score = await service.compute_score_for_link(business_id, link, link.connection_id)

    if not score:
        coverage = coverage_for(link.platform_source)
        reasons = {
            MEASURED: "No se pudo calcular: el SEO está apagado (global, de la plataforma o en el Mapa del Cerebro), "
                      "falta la conexión de la plataforma o la consulta a su API falló.",
            "web_audit": "Esta plataforma vive en un sitio propio: no tiene ranking de marketplace. "
                         "Se audita leyendo la página real en Auditoría SEO.",
            GUIDANCE_ONLY: "Todavía no hay conector ni auditoría para esta plataforma: consultá su guía de algoritmo.",
        }
        return {"computed": False, "coverage": coverage, "reason": reasons[coverage]}

    recommendations = await service.get_open_recommendations(business_id, link_id)

    return {
        "computed": True,
        "composite_score": score.composite_score,
        "measured_signal_pct": score.measured_signal_pct,
        "sub_scores": {
            "reputation_score": score.reputation_score,
            "conversion_score": score.conversion_score,
            "price_competitiveness_score": score.price_competitiveness_score,
            "listing_quality_score": score.listing_quality_score,
            "logistics_score": score.logistics_score,
            "engagement_score": score.engagement_score,
        },
        "raw_signals": score.raw_signals,
        "recommendations": [recommendation_payload(r, score.platform_name) for r in recommendations],
    }


@router.get("/publication-links/{link_id}/positioning", response_model=dict)
async def get_positioning_score(
    business_id: UUID,
    link_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the most recently computed positioning score + open recommendations for a link."""
    service = PositioningScoreService(db)
    score = await service.get_latest_score(business_id, link_id)

    if not score:
        raise HTTPException(status_code=404, detail="No positioning score computed yet for this link")

    recommendations = await service.get_open_recommendations(business_id, link_id)

    return {
        "link_id": str(link_id),
        "platform_name": score.platform_name,
        "composite_score": score.composite_score,
        "measured_signal_pct": score.measured_signal_pct,
        "computed_at": score.computed_at.isoformat(),
        "sub_scores": {
            "reputation_score": score.reputation_score,
            "conversion_score": score.conversion_score,
            "price_competitiveness_score": score.price_competitiveness_score,
            "listing_quality_score": score.listing_quality_score,
            "logistics_score": score.logistics_score,
            "engagement_score": score.engagement_score,
        },
        "raw_signals": score.raw_signals,
        "recommendations": [recommendation_payload(r, score.platform_name) for r in recommendations],
    }


@router.get("/publication-links/{link_id}/positioning/history", response_model=list[dict])
async def get_positioning_history(
    business_id: UUID,
    link_id: UUID,
    days: int = Query(30, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get positioning score history for a link (for trend charts)."""
    service = PositioningScoreService(db)
    history = await service.get_score_history(business_id, link_id, days)

    return [
        {
            "composite_score": s.composite_score,
            "measured_signal_pct": s.measured_signal_pct,
            "computed_at": s.computed_at.isoformat(),
        }
        for s in history
    ]


@router.get("/positioning/summary", response_model=dict)
async def get_positioning_summary(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Unified per-business positioning dashboard: latest score per platform link,
    plus a generic_web overlay from the web_presence on-page audit."""
    service = PositioningScoreService(db)
    return await service.get_business_summary(business_id)


@router.patch("/positioning/recommendations/{recommendation_id}/dismiss", response_model=dict)
async def dismiss_positioning_recommendation(
    business_id: UUID,
    recommendation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Dismiss an open positioning recommendation."""
    service = PositioningScoreService(db)
    dismissed = await service.dismiss_recommendation(business_id, recommendation_id)

    if not dismissed:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    return {"dismissed": True, "recommendation_id": str(recommendation_id)}


# ── Algorithm guide: how each platform ranks you, and how sure we are ──

@router.get("/positioning/algorithm-guide", response_model=dict)
async def get_algorithm_guide(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """How each platform ranks sellers, with every factor tagged as documented by the
    platform or reported by the seller community. Platforms this business actually
    publishes on come first."""
    result = await db.execute(
        select(PublicationLink.platform_source).where(PublicationLink.business_id == business_id).distinct()
    )
    in_use = {canonical_platform(p) or p for (p,) in result.all()}
    platforms = [
        {**profile_to_dict(p), "in_use": p.key in in_use}
        for p in PROFILES.values()
    ]
    platforms.sort(key=lambda p: (not p["in_use"], not p["researched"], p["label"]))
    return {"platforms": platforms}


@router.get("/positioning/algorithm-guide/{platform}", response_model=dict)
async def get_platform_algorithm_guide(
    business_id: UUID,
    platform: str,
    current_user: User = Depends(get_current_user),
):
    """One platform's algorithm guide (any spelling of the name works)."""
    profile = get_profile(platform)
    if not profile:
        raise HTTPException(status_code=404, detail="Plataforma sin guía de algoritmo")
    return profile_to_dict(profile)


# ── Store-level (storefront / brand) positioning ──

class ComputeStorePositioningRequest(BaseModel):
    platform: str
    connection_id: UUID  # for Amazon: the connection holding ADS API credentials, not SP-API
    external_id: str | None = None  # brand_entity_id override if not stored in the credentials


def _store_score_payload(score, recommendations) -> dict:
    return {
        "platform_name": score.platform_name,
        "composite_score": score.composite_score,
        "measured_signal_pct": score.measured_signal_pct,
        "computed_at": score.computed_at.isoformat(),
        "sub_scores": {
            "traffic_score": score.traffic_score,
            "engagement_score": score.engagement_score,
            "new_visitor_score": score.new_visitor_score,
            "content_performance_score": score.content_performance_score,
        },
        "raw_signals": score.raw_signals,
        "recommendations": [recommendation_payload(r, score.platform_name) for r in recommendations],
    }


@router.post("/store-positioning/compute", response_model=dict)
async def compute_store_positioning_score(
    business_id: UUID,
    data: ComputeStorePositioningRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Compute a fresh store-level positioning score (e.g. Amazon Brand Store)."""
    service = StorePositioningScoreService(db)
    score = await service.compute_store_score(
        business_id, data.platform, data.connection_id, data.external_id
    )

    if not score:
        return {
            "computed": False,
            "reason": (
                "No store connector for this platform, SEO disabled, invalid credentials "
                "(Amazon needs Ads API credentials, not SP-API), or the fetch failed."
            ),
        }

    recommendations = await service.get_open_store_recommendations(business_id, data.platform)
    return {"computed": True, **_store_score_payload(score, recommendations)}


@router.get("/store-positioning/{platform}", response_model=dict)
async def get_store_positioning_score(
    business_id: UUID,
    platform: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Latest store-level score + open recommendations + declared-storefront overlay."""
    service = StorePositioningScoreService(db)
    score = await service.get_latest_store_score(business_id, platform)
    storefront = await service.has_declared_storefront(business_id)

    if not score:
        raise HTTPException(status_code=404, detail="No store positioning score computed yet for this platform")

    recommendations = await service.get_open_store_recommendations(business_id, platform)
    return {**_store_score_payload(score, recommendations), "storefront": storefront}


@router.get("/store-positioning/{platform}/history", response_model=list[dict])
async def get_store_positioning_history(
    business_id: UUID,
    platform: str,
    days: int = Query(30, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Store-level score history (for trend charts)."""
    service = StorePositioningScoreService(db)
    history = await service.get_store_score_history(business_id, platform, days)

    return [
        {
            "composite_score": s.composite_score,
            "measured_signal_pct": s.measured_signal_pct,
            "computed_at": s.computed_at.isoformat(),
        }
        for s in history
    ]

