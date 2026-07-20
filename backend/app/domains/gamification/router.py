"""Gamification & Experience API Router"""

import uuid
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User

from app.domains.gamification.models import UserGamificationProfile, Achievement, UserAchievement, CelebrationEvent
from app.domains.gamification.schemas import (
    GamificationProfileResponse, AchievementResponse, UserAchievementResponse,
    CelebrationEventResponse, GardenStateResponse, CompanionMessageResponse,
    MoodCheckinRequest, MoodCheckinResponse, SaleRecordedResponse, LoginResponse,
    LeaderboardEntryResponse, UserRankResponse, NearbyUsersResponse, TeamStatsResponse,
)
from app.domains.gamification.service import GamificationEngine, GamificationSeeder
from app.domains.gamification.leaderboard import LeaderboardService, VALID_METRICS, DEFAULT_METRIC

router = APIRouter(prefix="/gamification", tags=["gamification"])


@router.get("/profile", response_model=GamificationProfileResponse)
async def get_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get user's gamification profile."""
    engine = GamificationEngine(db)
    profile = await engine.get_or_create_profile(
        current_user.id,
        current_user.business_id or current_user.id,
    )
    return profile


@router.post("/login", response_model=LoginResponse)
async def record_login(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Record daily login, update streaks, check achievements."""
    engine = GamificationEngine(db)
    business_id = current_user.business_id or current_user.id

    result = await engine.record_login(current_user.id, business_id)
    welcome_msg = await engine.get_companion_message(current_user.id, business_id, "welcome")

    return {
        **result,
        "welcome_message": welcome_msg,
    }


@router.get("/achievements", response_model=List[AchievementResponse])
async def list_achievements(
    db: AsyncSession = Depends(get_db),
):
    """List all available achievements."""
    from sqlalchemy import select
    result = await db.execute(select(Achievement).where(Achievement.is_active == True))
    return list(result.scalars().all())


@router.get("/my-achievements", response_model=List[UserAchievementResponse])
async def my_achievements(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List user's unlocked achievements."""
    from sqlalchemy import select
    result = await db.execute(
        select(UserAchievement).where(
            UserAchievement.user_id == current_user.id,
        ).order_by(UserAchievement.unlocked_at.desc())
    )
    return list(result.scalars().all())


@router.get("/celebrations/pending", response_model=List[CelebrationEventResponse])
async def get_pending_celebrations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get unshown celebration events."""
    engine = GamificationEngine(db)
    events = await engine.get_pending_celebrations(current_user.id)
    return events


@router.post("/celebrations/{celebration_id}/shown")
async def mark_celebration_shown(
    celebration_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark a celebration as shown."""
    engine = GamificationEngine(db)
    await engine.mark_celebration_shown(celebration_id)
    return {"status": "marked"}


@router.get("/garden", response_model=GardenStateResponse)
async def get_garden(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get user's Business Garden state."""
    engine = GamificationEngine(db)
    business_id = current_user.business_id or current_user.id
    profile = await engine.get_or_create_profile(current_user.id, business_id)
    return {
        "garden": profile.garden_state,
        "level": profile.level,
        "level_title": profile.level_title,
    }


@router.post("/garden/action")
async def garden_action(
    action: str,  # sale, lead, review, referral, milestone
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trigger a garden update action."""
    engine = GamificationEngine(db)
    business_id = current_user.business_id or current_user.id
    result = await engine.update_garden(current_user.id, business_id, action)
    return result


@router.get("/companion/message")
async def get_companion_message(
    context: str = "welcome",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a personalized companion message."""
    engine = GamificationEngine(db)
    business_id = current_user.business_id or current_user.id
    msg = await engine.get_companion_message(current_user.id, business_id, context)

    # Update companion state
    profile = await engine.get_or_create_profile(current_user.id, business_id)
    profile.companion_last_message = msg
    await db.commit()

    return {
        "message": msg,
        "mood": profile.companion_mood,
        "context": context,
    }


@router.post("/mood", response_model=MoodCheckinResponse)
async def mood_checkin(
    data: MoodCheckinRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Record daily mood check-in and get companion response."""
    from app.domains.gamification.models import DailyMoodLog

    log = DailyMoodLog(
        user_id=current_user.id,
        mood=data.mood,
        energy_level=data.energy_level,
        notes=data.notes,
    )

    # Generate AI companion response
    try:
        from app.domains.agents.ai_reply import generate_raw_ai_response
        companion_response = await generate_raw_ai_response(
            db=db,
            business_id=current_user.business_id or current_user.id,
            system_prompt="Eres Selia, la compañera AI de un emprendedor. Respondes a su check-in de humor con empatía, motivación y calidez. Máximo 2 oraciones. Tono: amiga cercana, no robótica.",
            user_prompt=f"Mi humor hoy es: {data.mood}. Nivel de energía: {data.energy_level}/10. Notas: {data.notes or 'Ninguna'}. Respondeme como mi compañera.",
            max_tokens=200,
            temperature=0.8,
        )
        log.ai_response = companion_response or "Entendido. Estoy acá para lo que necesites. 💪"
    except Exception:
        log.ai_response = "Entendido. Estoy acá para lo que necesites. 💪"

    db.add(log)
    await db.commit()
    await db.refresh(log)

    # Update profile mood
    engine = GamificationEngine(db)
    profile = await engine.get_or_create_profile(
        current_user.id,
        current_user.business_id or current_user.id,
    )
    profile.user_mood_today = data.mood
    profile.mood_history.append({
        "date": log.created_at.isoformat(),
        "mood": data.mood,
        "energy": data.energy_level,
    })
    await db.commit()

    return log


@router.get("/mood/history")
async def mood_history(
    limit: int = 30,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get mood history."""
    from sqlalchemy import select, desc
    from app.domains.gamification.models import DailyMoodLog
    result = await db.execute(
        select(DailyMoodLog).where(
            DailyMoodLog.user_id == current_user.id,
        ).order_by(desc(DailyMoodLog.created_at)).limit(limit)
    )
    return list(result.scalars().all())


@router.post("/seed-achievements")
async def seed_achievements(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Seed default achievements (admin only)."""
    await GamificationSeeder.seed_achievements(db)
    return {"status": "seeded"}


# ============================================================
#  Leaderboard
# ============================================================

@router.get("/leaderboard", response_model=List[LeaderboardEntryResponse])
async def get_leaderboard(
    business_id: uuid.UUID,
    metric: str = DEFAULT_METRIC,
    period: str = "all_time",
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the social leaderboard for a business."""
    svc = LeaderboardService(db)
    has_access = await svc._check_business_access(business_id, current_user.id)
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes acceso a este negocio.",
        )
    return await svc.get_leaderboard(business_id, metric, period, limit)


@router.get("/leaderboard/me", response_model=UserRankResponse)
async def get_my_rank(
    business_id: uuid.UUID,
    metric: str = DEFAULT_METRIC,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get current user's rank within their business."""
    svc = LeaderboardService(db)
    has_access = await svc._check_business_access(business_id, current_user.id)
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes acceso a este negocio.",
        )
    return await svc.get_user_rank(business_id, current_user.id, metric)


@router.get("/leaderboard/nearby", response_model=NearbyUsersResponse)
async def get_nearby(
    business_id: uuid.UUID,
    metric: str = DEFAULT_METRIC,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get users ranked near the current user (±2 positions)."""
    svc = LeaderboardService(db)
    has_access = await svc._check_business_access(business_id, current_user.id)
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes acceso a este negocio.",
        )
    return await svc.get_nearby_users(business_id, current_user.id, metric, radius=2)


@router.get("/leaderboard/team-stats", response_model=TeamStatsResponse)
async def get_team_stats(
    business_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get aggregated team stats for a business."""
    svc = LeaderboardService(db)
    has_access = await svc._check_business_access(business_id, current_user.id)
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes acceso a este negocio.",
        )
    return await svc.get_team_stats(business_id)
