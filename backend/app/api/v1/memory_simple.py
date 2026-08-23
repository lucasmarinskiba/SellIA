"""Minimal memory endpoint for testing"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.domains.users.models import User

router = APIRouter()


@router.get("/me")
async def get_my_memory(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get user memory"""
    return {
        "user_id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "engagement_score": 0.5,
        "satisfaction_score": 0.0,
        "churn_risk_score": 0.0,
        "total_messages": 0,
        "total_conversations": 0,
        "industry_focus": None,
        "preferred_tone": None,
        "business_stage": None,
        "key_interests": [],
        "key_challenges": [],
    }


@router.patch("/me")
async def update_my_memory(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update user memory"""
    return {
        "user_id": str(current_user.id),
        "industry_focus": data.get("industry_focus"),
        "preferred_tone": data.get("preferred_tone"),
    }
