"""FOMO+SEO Integrated API."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cached
from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.fomo_seo.service import A_B_TestService, FOMOSEOCopyService
from app.domains.users.models import User

router = APIRouter(prefix="/{business_id}/fomo-seo", tags=["FOMO+SEO"])


@router.post("/copy/generate")
async def generate_copy(
    business_id: UUID,
    title: Annotated[str, Query(min_length=10, max_length=255)],
    meta_description: Annotated[str, Query(min_length=50, max_length=160)],
    short_description: Annotated[str, Query(min_length=50, max_length=500)],
    long_description: Annotated[str, Query(min_length=100)],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    product_id: UUID | None = None,
    call_to_action: Annotated[str, Query()] = "Buy Now",
    urgency_trigger: str | None = None,
    social_proof: str | None = None,
    scarcity_message: str | None = None,
    platform: Annotated[str, Query()] = "shopify",
):
    """Generate FOMO+SEO optimized copy."""
    svc = FOMOSEOCopyService(db)
    copy = await svc.generate_copy(
        business_id,
        product_id,
        title,
        meta_description,
        short_description,
        long_description,
        call_to_action=call_to_action,
        urgency_trigger=urgency_trigger,
        social_proof_element=social_proof,
        scarcity_message=scarcity_message,
        platform=platform,
    )
    return {
        "copy_id": copy.id,
        "seo_score": copy.seo_score,
        "ctr_score": copy.ctr_score,
        "title": copy.title,
        "meta_description": copy.meta_description,
    }


@router.get("/copy")
@cached(ttl_seconds=3600, key_prefix="fomo_copy")
async def list_copy(
    business_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    platform: Annotated[str | None, Query()] = None,
    status: Annotated[str, Query()] = "active",
):
    """List FOMO+SEO copy (cached 1h)."""
    svc = FOMOSEOCopyService(db)
    copies = await svc.list_copy(business_id, platform, status)
    return {
        "total": len(copies),
        "copies": [
            {
                "id": c.id,
                "title": c.title,
                "seo_score": c.seo_score,
                "ctr_score": c.ctr_score,
                "urgency_trigger": c.urgency_trigger,
            }
            for c in copies
        ],
    }


@router.post("/ab-test/create")
async def create_ab_test(
    business_id: UUID,
    copy_id: UUID,
    variant_a_title: Annotated[str, Query(max_length=255)],
    variant_b_title: Annotated[str, Query(max_length=255)],
    variant_a_desc: Annotated[str, Query(max_length=500)],
    variant_b_desc: Annotated[str, Query(max_length=500)],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Create A/B test for copy variants."""
    svc = A_B_TestService(db)
    test = await svc.create_test(
        business_id,
        copy_id,
        variant_a_title,
        variant_b_title,
        variant_a_desc,
        variant_b_desc,
    )
    return {
        "test_id": test.id,
        "status": "active",
        "variant_a": {"title": test.variant_a_title},
        "variant_b": {"title": test.variant_b_title},
    }


@router.get("/ab-test/active")
@cached(ttl_seconds=600, key_prefix="ab_tests")
async def list_active_tests(
    business_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """List active A/B tests (cached 10min)."""
    svc = A_B_TestService(db)
    tests = await svc.list_tests(business_id)
    return {
        "active_tests": len(tests),
        "tests": [
            {
                "test_id": t.id,
                "winner": t.winner,
                "variant_a_ctr": t.variant_a_ctr,
                "variant_b_ctr": t.variant_b_ctr,
            }
            for t in tests
        ],
    }


@router.patch("/ab-test/{test_id}/results")
async def update_test_results(
    business_id: UUID,
    test_id: UUID,
    variant_a_impressions: Annotated[int, Query(ge=0)],
    variant_a_clicks: Annotated[int, Query(ge=0)],
    variant_a_conversions: Annotated[int, Query(ge=0)],
    variant_b_impressions: Annotated[int, Query(ge=0)],
    variant_b_clicks: Annotated[int, Query(ge=0)],
    variant_b_conversions: Annotated[int, Query(ge=0)],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Update A/B test results."""
    svc = A_B_TestService(db)
    test = await svc.update_results(
        test_id,
        variant_a_impressions,
        variant_a_clicks,
        variant_a_conversions,
        variant_b_impressions,
        variant_b_clicks,
        variant_b_conversions,
    )
    return {
        "test_id": test.id,
        "winner": test.winner,
        "variant_a_conversion_rate": f"{test.variant_a_conversion_rate:.2f}%",
        "variant_b_conversion_rate": f"{test.variant_b_conversion_rate:.2f}%",
    }
