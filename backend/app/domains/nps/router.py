"""
NPS & Feedback Router
"""

from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.nps.models import FeedbackNPSResponse, FeedbackItem

router = APIRouter(prefix="/feedback", tags=["feedback"])


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


@router.post("/nps")
async def submit_nps(
    data: dict,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    nps = FeedbackNPSResponse(
        user_id=current_user.id,
        score=data.get("score", 0),
        feedback=data.get("feedback"),
        category=data.get("category", "product"),
        follow_up_allowed=data.get("follow_up_allowed", False),
        follow_up_email=data.get("follow_up_email"),
    )
    db.add(nps)
    await db.commit()
    return {"message": "Gracias por tu feedback"}


@router.get("/nps/stats")
async def nps_stats(db: Annotated[AsyncSession, Depends(get_db)]):
    from sqlalchemy import func, select
    result = await db.execute(select(func.avg(FeedbackNPSResponse.score)))
    avg_score = result.scalar() or 0

    promoters = await db.execute(select(func.count(FeedbackNPSResponse.id)).where(FeedbackNPSResponse.score >= 9))
    passives = await db.execute(select(func.count(FeedbackNPSResponse.id)).where(FeedbackNPSResponse.score.between(7, 8)))
    detractors = await db.execute(select(func.count(FeedbackNPSResponse.id)).where(FeedbackNPSResponse.score <= 6))

    total = promoters.scalar() + passives.scalar() + detractors.scalar()
    nps_score = round(((promoters.scalar() - detractors.scalar()) / total) * 100, 1) if total else 0

    return {
        "avg_score": round(avg_score, 1),
        "nps_score": nps_score,
        "promoters": promoters.scalar(),
        "passives": passives.scalar(),
        "detractors": detractors.scalar(),
        "total_responses": total,
    }


@router.post("/general")
async def submit_feedback(
    data: dict,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    fb = FeedbackItem(
        user_id=current_user.id,
        feedback_type=data.get("feedback_type", "other"),
        message=data.get("message"),
        context=data.get("context"),
        screenshot_url=data.get("screenshot_url"),
    )
    db.add(fb)
    await db.commit()
    return {"message": "Feedback enviado"}
