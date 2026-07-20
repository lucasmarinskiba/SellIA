"""
Referral Service
"""

import uuid
import secrets
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.domains.referrals.models import ReferralCode, ReferralTracking


async def get_or_create_referral_code(db: AsyncSession, user_id: uuid.UUID) -> ReferralCode:
    result = await db.execute(select(ReferralCode).where(ReferralCode.user_id == user_id))
    code = result.scalar_one_or_none()
    if not code:
        new_code = secrets.token_urlsafe(8).upper()[:10]
        code = ReferralCode(
            user_id=user_id,
            code=new_code,
            link=f"https://app.sellia.com/?ref={new_code}",
        )
        db.add(code)
        await db.commit()
        await db.refresh(code)
    return code


async def track_click(db: AsyncSession, code_str: str, ip: Optional[str], ua: Optional[str]) -> Optional[ReferralTracking]:
    result = await db.execute(select(ReferralCode).where(ReferralCode.code == code_str))
    code = result.scalar_one_or_none()
    if not code:
        return None

    code.total_clicks += 1
    track = ReferralTracking(
        referrer_id=code.user_id,
        referral_code_id=code.id,
        ip_address=ip,
        user_agent=ua,
    )
    db.add(track)
    await db.commit()
    await db.refresh(track)
    return track


async def track_signup(db: AsyncSession, tracking_id: uuid.UUID, new_user_id: uuid.UUID):
    result = await db.execute(select(ReferralTracking).where(ReferralTracking.id == tracking_id))
    track = result.scalar_one_or_none()
    if not track:
        return

    track.referred_user_id = new_user_id
    track.signed_up_at = datetime.now(timezone.utc)

    # Update referrer stats
    code_result = await db.execute(select(ReferralCode).where(ReferralCode.id == track.referral_code_id))
    code = code_result.scalar_one_or_none()
    if code:
        code.total_signups += 1

    await db.commit()


async def track_conversion(db: AsyncSession, referred_user_id: uuid.UUID, amount: float):
    """Call this when a referred user makes their first purchase."""
    result = await db.execute(
        select(ReferralTracking).where(
            ReferralTracking.referred_user_id == referred_user_id,
            ReferralTracking.converted_at.is_(None),
        )
    )
    track = result.scalar_one_or_none()
    if not track:
        return

    track.converted_at = datetime.now(timezone.utc)
    track.first_purchase_amount = amount
    track.reward_amount = min(amount * 0.20, 50)  # 20% up to $50
    track.reward_status = "pending"

    code_result = await db.execute(select(ReferralCode).where(ReferralCode.id == track.referral_code_id))
    code = code_result.scalar_one_or_none()
    if code:
        code.total_conversions += 1
        code.total_revenue_generated += amount
        code.total_credits_earned += track.reward_amount

    await db.commit()


async def get_referral_stats(db: AsyncSession, user_id: uuid.UUID) -> dict:
    result = await db.execute(select(ReferralCode).where(ReferralCode.user_id == user_id))
    code = result.scalar_one_or_none()
    if not code:
        return {"has_code": False}

    return {
        "has_code": True,
        "code": code.code,
        "link": code.link,
        "total_clicks": code.total_clicks,
        "total_signups": code.total_signups,
        "total_conversions": code.total_conversions,
        "total_revenue_generated": float(code.total_revenue_generated),
        "total_credits_earned": float(code.total_credits_earned),
    }
