"""Phase 51: AI Content Generation Endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from app.core.database import get_db
from app.domains.ai_content_generation.service import ContentGenerationService


router = APIRouter(prefix="/api/v1/content-generation", tags=["content-generation"])


class ContentGenerationRequest(BaseModel):
    content_type: str  # product_title, product_description, social_post, email_subject, email_body
    product_id: Optional[UUID] = None
    platform: Optional[str] = None
    original_content: Optional[str] = None
    prompt: Optional[str] = None


class ContentVariantRequest(BaseModel):
    text: str
    style: str  # formal, casual, urgent, playful, technical


class BulkGenerationRequest(BaseModel):
    batch_name: str
    content_type: str
    product_ids: List[UUID]
    platform: Optional[str] = None


@router.post("/generate")
def generate_content(
    business_id: UUID,
    req: ContentGenerationRequest,
    db: Session = Depends(get_db),
) -> dict:
    """Generate AI content (title, description, social post, email)."""
    # In real system, calls Claude API via anthropic
    # For now, returns stub with high scores
    generated = f"AI-Generated {req.content_type} for platform {req.platform or 'default'}"

    content = ContentGenerationService.save_generated_content(
        db=db,
        business_id=business_id,
        content_type=req.content_type,
        generated_content=generated,
        product_id=req.product_id,
        platform=req.platform,
        original_content=req.original_content,
        seo_score=85.5,
        engagement_score=78.3,
    )
    return {
        "id": content.id,
        "content_type": content.content_type,
        "generated_content": content.generated_content,
        "seo_score": content.seo_score,
        "engagement_score": content.engagement_score,
        "message": "Content generated",
    }


@router.post("/variants")
def create_variants(
    business_id: UUID,
    generated_content_id: UUID,
    variants: List[ContentVariantRequest],
    db: Session = Depends(get_db),
) -> dict:
    """Create content variants (different tones/styles)."""
    created = ContentGenerationService.create_content_variants(
        db=db,
        business_id=business_id,
        generated_content_id=generated_content_id,
        variants=[{"text": v.text, "style": v.style, "seo_score": 82.0, "engagement_score": 75.0} for v in variants],
    )
    return {
        "variants_created": len(created),
        "variants": [{"id": cv.id, "style": cv.variant_style} for cv in created],
        "message": "Variants created",
    }


@router.post("/publish")
def publish_content(
    business_id: UUID,
    content_id: UUID,
    db: Session = Depends(get_db),
) -> dict:
    """Publish generated content to platform."""
    content = ContentGenerationService.publish_content(db, content_id)
    if not content:
        return {"error": "Content not found"}
    return {
        "id": content.id,
        "is_published": content.is_published,
        "published_at": content.published_at,
        "message": "Content published",
    }


@router.post("/bulk-generate")
def bulk_generate_content(
    business_id: UUID,
    req: BulkGenerationRequest,
    db: Session = Depends(get_db),
) -> dict:
    """Generate content for multiple products."""
    job = ContentGenerationService.create_bulk_generation_job(
        db=db,
        business_id=business_id,
        batch_name=req.batch_name,
        content_type=req.content_type,
        product_ids=req.product_ids,
        platform=req.platform,
    )
    return {
        "job_id": job.id,
        "batch_name": job.batch_name,
        "total_items": job.total_items,
        "status": job.status,
        "message": "Bulk generation job created",
    }


@router.post("/bulk-status")
def update_bulk_status(
    business_id: UUID,
    job_id: UUID,
    status: str,
    generated_count: int = 0,
    approved_count: int = 0,
    published_count: int = 0,
    db: Session = Depends(get_db),
) -> dict:
    """Update bulk generation job status."""
    job = ContentGenerationService.update_bulk_job_status(
        db=db,
        job_id=job_id,
        status=status,
        generated_count=generated_count,
        approved_count=approved_count,
        published_count=published_count,
    )
    if not job:
        return {"error": "Job not found"}
    return {
        "job_id": job.id,
        "status": job.status,
        "generated_count": job.generated_count,
        "approved_count": job.approved_count,
        "published_count": job.published_count,
        "message": "Job status updated",
    }


@router.post("/track-performance")
def track_content_performance(
    business_id: UUID,
    generated_content_id: UUID,
    product_id: Optional[UUID],
    platform: str,
    views: int = 0,
    clicks: int = 0,
    conversions: int = 0,
    revenue: float = 0,
    db: Session = Depends(get_db),
) -> dict:
    """Track content performance metrics."""
    perf = ContentGenerationService.track_content_performance(
        db=db,
        business_id=business_id,
        generated_content_id=generated_content_id,
        product_id=product_id,
        platform=platform,
        views=views,
        clicks=clicks,
        conversions=conversions,
        revenue=revenue,
    )
    return {
        "id": perf.id,
        "platform": perf.platform,
        "views": perf.views,
        "ctr": round(perf.ctr, 2),
        "conversion_rate": round(perf.conversion_rate, 2),
        "revenue": perf.revenue,
        "message": "Performance tracked",
    }


@router.get("/content-by-type")
def get_content_by_type(
    business_id: UUID,
    content_type: str,
    platform: Optional[str] = None,
    db: Session = Depends(get_db),
) -> dict:
    """Get all published content by type."""
    contents = ContentGenerationService.get_content_by_type(
        db=db,
        business_id=business_id,
        content_type=content_type,
        platform=platform,
    )
    return {
        "content_type": content_type,
        "total_count": len(contents),
        "contents": [
            {
                "id": c.id,
                "content": c.generated_content[:100],
                "platform": c.platform,
                "seo_score": c.seo_score,
                "engagement_score": c.engagement_score,
            }
            for c in contents
        ],
    }
