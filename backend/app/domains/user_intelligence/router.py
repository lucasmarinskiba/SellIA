"""Phase X9: AI User Intelligence Agent API."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.domains.user_intelligence.service import UserIntelligenceAgent
from app.domains.user_intelligence.models import UserRiskProfile


router = APIRouter(prefix="/api/v1/user-intelligence", tags=["user-intelligence"])


@router.post("/profile-user")
async def profile_user(
    user_id: str,
    email: str,
    company_name: str,
    engagement_data: dict,  # {email_opens, clicks, case_study_views, demo_requests}
    company_data: dict,  # {industry, company_size, role, budget_approved}
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create comprehensive AI user profile."""
    profile = await UserIntelligenceAgent.profile_user(
        db, user_id, email, company_name, engagement_data, company_data
    )
    return {
        "user_id": profile.user_id,
        "personality_type": profile.personality_type,
        "conversion_probability": profile.estimated_conversion_probability,
        "recommended_messaging": profile.recommended_messaging,
        "next_best_action": profile.next_best_action,
        "scarcity_responsiveness": profile.scarcity_responsiveness,
        "decision_velocity": profile.decision_velocity,
        "social_proof_sensitivity": profile.social_proof_sensitivity,
    }


@router.get("/get-personalized-messaging/{user_id}")
async def get_personalized_messaging(
    user_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get personalized messaging strategy for user."""
    # In real implementation: fetch profile from DB, generate messaging
    return {
        "user_id": user_id,
        "subject": "Generated based on personality type",
        "hook": "Personalized hook for this user's motivation",
        "cta": "Custom call-to-action",
    }


@router.post("/update-journey/{user_id}/{stage}")
async def update_journey_stage(
    user_id: str,
    stage: str,  # awareness, consideration, decision, onboarding, retention
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Move user through journey stages."""
    journey = await UserIntelligenceAgent.update_journey_stage(db, user_id, stage)
    return {
        "user_id": journey.user_id,
        "stage": journey.stage,
        "entry_date": journey.entry_date,
        "momentum": journey.momentum,
    }


@router.get("/churn-risk/{user_id}")
async def get_churn_risk(
    user_id: str,
) -> dict:
    """Predict churn probability for customer."""
    # In real: fetch profile, calculate risk
    return {
        "user_id": user_id,
        "churn_risk_score": 0.15,  # 15% chance of churning
        "risk_level": "low",
        "recommended_retention_tactic": "upsell_expansion",
        "suggested_actions": [
            "Schedule QBR with account manager",
            "Send success metrics report",
            "Invite to VIP training webinar"
        ],
    }
