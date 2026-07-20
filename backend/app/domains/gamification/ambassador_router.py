"""
Ambassador & Certification Router
"""

from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.gamification.ambassador_service import list_certifications, get_user_certifications, get_or_create_expert_profile, publish_profile

router = APIRouter(prefix="/ambassador", tags=["ambassador"])


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


@router.get("/certifications")
async def get_all_certifications(db: Annotated[AsyncSession, Depends(get_db)]):
    certs = await list_certifications(db)
    return [
        {
            "id": c.id,
            "slug": c.slug,
            "name": c.name,
            "description": c.description,
            "level": c.level,
            "category": c.category,
            "badge_image_url": c.badge_image_url,
            "badge_color": c.badge_color,
        }
        for c in certs
    ]


@router.get("/my-certifications")
async def get_my_certs(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    certs = await get_user_certifications(db, current_user.id)
    return [
        {
            "id": c.id,
            "program_name": c.program.name if c.program else None,
            "status": c.status,
            "progress_percent": c.progress_percent,
            "completed_at": c.completed_at,
            "certificate_id": c.certificate_id,
            "is_public": c.is_public,
        }
        for c in certs
    ]


@router.get("/profile")
async def get_profile(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    profile = await get_or_create_expert_profile(db, current_user.id)
    return {
        "slug": profile.slug,
        "headline": profile.headline,
        "bio": profile.bio,
        "specialty": profile.specialty,
        "total_sales_helped": profile.total_sales_helped,
        "total_revenue_helped": profile.total_revenue_helped,
        "testimonials": profile.testimonials,
        "social_links": profile.social_links,
        "displayed_badges": profile.displayed_badges,
        "is_published": profile.is_published,
        "view_count": profile.view_count,
    }


@router.post("/profile/publish")
async def publish_expert_profile(
    data: dict,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    profile = await publish_profile(db, current_user.id, data)
    return {"message": "Profile published", "slug": profile.slug, "url": f"/expert/{profile.slug}"}
