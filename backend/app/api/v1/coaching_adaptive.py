"""Phases 23-24: Entrepreneurship Coach & Adaptive Architecture."""

from fastapi import APIRouter, Query, Body
from typing import Dict, Any
import logging

from app.domains.coaching.entrepreneur_coach import EntrepreneurCoachAgent, EntrepreneurStage
from app.domains.personalization.adaptive_engine import AdaptiveEngine, UserSegment

router = APIRouter(tags=["coaching-adaptive"])
logger = logging.getLogger(__name__)

coach_agent = EntrepreneurCoachAgent()
adaptive_engine = AdaptiveEngine()


# ============================================================
# Phase 23: Entrepreneurship Coach Agent
# ============================================================


@router.post("/coach/assess/{user_id}")
async def assess_entrepreneur(
    user_id: str,
    days_in_business: int = Query(...),
    leads_generated: int = Query(0),
    deals_closed: int = Query(0),
    revenue: float = Query(0.0),
) -> Dict[str, Any]:
    """Assess entrepreneur stage and create coaching profile."""

    business_data = {
        "days_in_business": days_in_business,
        "leads_generated": leads_generated,
        "deals_closed": deals_closed,
        "revenue": revenue
    }

    profile = coach_agent.assess_entrepreneur(user_id, business_data)

    return {
        "status": "success",
        "user_id": user_id,
        "stage": profile.stage.value,
        "days_in_business": profile.days_in_business,
        "metrics": {
            "leads": profile.leads_generated,
            "deals": profile.deals_closed,
            "revenue": profile.revenue
        },
        "challenges": profile.challenges,
        "motivation_level": profile.motivation_level
    }


@router.get("/coach/daily-coaching/{user_id}")
async def get_daily_coaching(user_id: str) -> Dict[str, Any]:
    """Get personalized daily coaching message."""

    message = coach_agent.get_daily_coaching(user_id)

    return {
        "status": "success",
        "user_id": user_id,
        "coaching": {
            "title": message.title,
            "message": message.body,
            "topic": message.topic.value,
            "urgency": message.urgency,
            "action_item": message.action_item,
            "resource": message.resource_url
        }
    }


@router.get("/coach/milestones/{user_id}")
async def get_milestones(user_id: str) -> Dict[str, Any]:
    """Track entrepreneur milestones."""

    milestones = coach_agent.get_milestone_tracking(user_id)

    return {
        "status": "success",
        "user_id": user_id,
        "milestones": milestones
    }


@router.post("/coach/emergency-support/{user_id}")
async def emergency_support(
    user_id: str,
    issue: str = Query(...)
) -> Dict[str, Any]:
    """Emergency support for struggling entrepreneurs."""

    # Emergency scenarios
    emergency_responses = {
        "no_leads": "Focus on 2 sources: 1) Direct outreach to 20 people/day, 2) Google Maps optimization",
        "no_sales": "Lower your price, ask for objections, follow up 3x before giving up",
        "burnt_out": "Take a day off. Success isn't linear. Most win after month 2-3. You're close.",
        "competition": "Your unique advantage exists. Define it: faster? Cheaper? Better? Niche? Focus there.",
        "pricing": "Start low ($100-500), increase after 5 sales. Prove model works first."
    }

    response = emergency_responses.get(issue, "You've got this. Every entrepreneur struggles. Let's fix it together.")

    return {
        "status": "success",
        "user_id": user_id,
        "issue": issue,
        "emergency_support": response,
        "escalate_to_human": False,
        "resources": [
            "Entrepreneurship mindset guide",
            "Sales objection handling",
            "Pricing strategy playbook"
        ]
    }


# ============================================================
# Phase 24: Adaptive Backend Architecture
# ============================================================


@router.post("/adaptive/analyze-user/{user_id}")
async def analyze_user_needs(
    user_id: str,
    days_in_business: int = Query(...),
    leads_generated: int = Query(0),
    deals_closed: int = Query(0),
    hours_since_last_activity: int = Query(999)
) -> Dict[str, Any]:
    """Analyze user and determine personalization strategy."""

    business_metrics = {
        "days_in_business": days_in_business,
        "leads_generated": leads_generated,
        "deals_closed": deals_closed,
        "hours_since_last_activity": hours_since_last_activity
    }

    context = adaptive_engine.analyze_user(user_id, business_metrics)

    return {
        "status": "success",
        "user_id": user_id,
        "personalization": {
            "segment": context.segment.value,
            "primary_need": context.primary_need.value,
            "engagement_score": context.engagement_score,
            "urgency": context.urgency,
            "preferred_content": context.preferred_content_type
        }
    }


@router.get("/adaptive/personalization/{user_id}")
async def get_personalization_summary(user_id: str) -> Dict[str, Any]:
    """Get full personalization summary for user."""

    summary = adaptive_engine.get_personalization_summary(user_id)

    if not summary:
        return {
            "status": "error",
            "message": "User not analyzed. Call /adaptive/analyze-user first."
        }

    return {
        "status": "success",
        "personalization": summary
    }


@router.post("/adaptive/personalize-response")
async def personalize_response(
    user_id: str = Query(...),
    endpoint_name: str = Query(...),
    base_response: Dict[str, Any] = Body(...)
) -> Dict[str, Any]:
    """Personalize any endpoint response based on user context."""

    adapted = adaptive_engine.adapt_endpoint_response(user_id, endpoint_name, base_response)

    return {
        "status": "success",
        "user_id": user_id,
        "endpoint": endpoint_name,
        "personalized": adapted.personalized,
        "adaptation": {
            "content_type": adapted.content_type,
            "urgency": adapted.urgency_level,
            "next_action": adapted.recommended_next_action,
            "metrics": adapted.metrics
        }
    }


@router.get("/adaptive/segment-features/{user_id}")
async def get_segment_features(user_id: str) -> Dict[str, Any]:
    """Get features and settings for user's segment."""

    if user_id not in adaptive_engine.user_profiles:
        return {"status": "error", "message": "User not analyzed"}

    context = adaptive_engine.user_profiles[user_id]
    config = adaptive_engine.segment_configs.get(context.segment.value, {})

    return {
        "status": "success",
        "user_id": user_id,
        "segment": context.segment.value,
        "features": {
            "enabled_features": config.get("features", []),
            "messaging_style": config.get("messaging", ""),
            "update_frequency": config.get("frequency", ""),
            "complexity_level": config.get("complexity", "")
        }
    }
