"""
Product Tour Router
"""

from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.product_tours.models import TourStep, UserTourProgress

router = APIRouter(prefix="/tours", tags=["tours"])


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


@router.get("/{tour_id}/steps")
async def get_tour_steps(tour_id: str, db: Annotated[AsyncSession, Depends(get_db)]):
    from sqlalchemy import select
    result = await db.execute(
        select(TourStep).where(TourStep.tour_id == tour_id, TourStep.is_active == True).order_by(TourStep.step_order)
    )
    steps = result.scalars().all()
    return [
        {
            "step_order": s.step_order,
            "title": s.title,
            "content": s.content,
            "target_element": s.target_element,
            "placement": s.placement,
            "action_type": s.action_type,
            "action_target": s.action_target,
            "delay_ms": s.delay_ms,
            "image_url": s.image_url,
            "accent_color": s.accent_color,
        }
        for s in steps
    ]


@router.post("/{tour_id}/progress")
async def update_progress(
    tour_id: str,
    data: dict,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    from sqlalchemy import select
    result = await db.execute(
        select(UserTourProgress).where(
            UserTourProgress.user_id == current_user.id,
            UserTourProgress.tour_id == tour_id,
        )
    )
    progress = result.scalar_one_or_none()
    if not progress:
        progress = UserTourProgress(
            user_id=current_user.id,
            tour_id=tour_id,
            total_steps=data.get("total_steps", 0),
            current_step=data.get("current_step", 0),
            started_from_page=data.get("page"),
        )
        db.add(progress)
    else:
        progress.current_step = data.get("current_step", progress.current_step)
        progress.is_completed = data.get("is_completed", False)
        progress.is_skipped = data.get("is_skipped", False)
        if progress.is_completed:
            from datetime import datetime, timezone
            progress.completed_at = datetime.now(timezone.utc)

    await db.commit()
    return {"current_step": progress.current_step, "is_completed": progress.is_completed}


@router.get("/my-progress")
async def get_my_progress(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    from sqlalchemy import select
    result = await db.execute(
        select(UserTourProgress).where(UserTourProgress.user_id == current_user.id)
    )
    progress = result.scalars().all()
    return [
        {
            "tour_id": p.tour_id,
            "current_step": p.current_step,
            "total_steps": p.total_steps,
            "is_completed": p.is_completed,
            "is_skipped": p.is_skipped,
            "completed_at": p.completed_at,
        }
        for p in progress
    ]
