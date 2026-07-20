"""
Ambassador & Certification Service
"""

import uuid
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.domains.gamification.ambassador_models import CertificationProgram, UserCertification, PublicExpertProfile


async def list_certifications(db: AsyncSession) -> List[CertificationProgram]:
    result = await db.execute(select(CertificationProgram).where(CertificationProgram.is_active == True))
    return result.scalars().all()


async def get_user_certifications(db: AsyncSession, user_id: uuid.UUID) -> List[UserCertification]:
    result = await db.execute(
        select(UserCertification)
        .where(UserCertification.user_id == user_id)
        .order_by(desc(UserCertification.created_at))
    )
    return result.scalars().all()


async def get_or_create_expert_profile(db: AsyncSession, user_id: uuid.UUID) -> PublicExpertProfile:
    result = await db.execute(select(PublicExpertProfile).where(PublicExpertProfile.user_id == user_id))
    profile = result.scalar_one_or_none()
    if not profile:
        profile = PublicExpertProfile(
            user_id=user_id,
            slug=f"expert-{str(user_id)[:8]}",
            headline="Experto en Ventas con IA",
            bio="Transformando negocios con automatización inteligente.",
            specialty="E-commerce AI",
        )
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
    return profile


async def publish_profile(db: AsyncSession, user_id: uuid.UUID, data: dict) -> PublicExpertProfile:
    profile = await get_or_create_expert_profile(db, user_id)
    for field, value in data.items():
        if value is not None and hasattr(profile, field):
            setattr(profile, field, value)
    profile.is_published = True
    await db.commit()
    await db.refresh(profile)
    return profile
