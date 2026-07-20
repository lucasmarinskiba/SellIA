"""
Referral Router
"""

from typing import Annotated, Optional
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.referrals import service as referral_service

router = APIRouter(prefix="/referrals", tags=["referrals"])


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


@router.get("/my-code")
async def get_my_code(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    code = await referral_service.get_or_create_referral_code(db, current_user.id)
    stats = await referral_service.get_referral_stats(db, current_user.id)
    return stats


@router.post("/track-click/{code}")
async def track_click(
    code: str,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    track = await referral_service.track_click(db, code, ip, ua)
    if not track:
        return {"error": "Invalid code"}
    return {"tracking_id": track.id, "message": "Click tracked"}


@router.get("/stats")
async def get_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await referral_service.get_referral_stats(db, current_user.id)
