"""Deal Intelligence API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.domains.enterprise.deal_intelligence import DealIntelligenceManager
from backend.celery_app import predict_deal_probability, calculate_deal_health

router = APIRouter(prefix="/api/v1/intelligence", tags=["deal-intelligence"])


# ============================================================
# REQUEST/RESPONSE MODELS
# ============================================================


class StakeholderResponse(BaseModel):
    person_id: str
    email: str
    name: str
    title: str
    buyer_role: str
    influence_level: int
    engagement_score: float
    email_open_count: int
    meeting_count: int
    last_activity: Optional[str]


class AddStakeholderRequest(BaseModel):
    person_id: str
    email: str
    name: str
    title: str
    buyer_role: str = "influencer"
    influence_level: int = 5


class EngagementEventRequest(BaseModel):
    event_type: str  # email_open, call, meeting, etc
    event_details: Optional[dict] = None


class ProbabilityResponse(BaseModel):
    close_probability: float
    confidence_level: float
    probability_low: float
    probability_high: float
    model_version: str


class HealthComponentScore(BaseModel):
    score: int
    status: str


class DealHealthResponse(BaseModel):
    health_score: int
    health_status: str
    engagement_health: int
    momentum_health: int
    buyer_health: int
    competition_health: int
    risk_indicators: dict
    recommended_actions: List[dict]


class DealIntelligenceResponse(BaseModel):
    deal_id: str
    stakeholders: List[StakeholderResponse]
    probability: Optional[ProbabilityResponse]
    health: Optional[DealHealthResponse]


# ============================================================
# ENDPOINTS
# ============================================================


@router.get("/deal/{deal_id}")
def get_deal_intelligence(
    deal_id: str,
    db: Session = Depends(get_db),
):
    """Get complete deal intelligence (stakeholders + probability + health)."""
    manager = DealIntelligenceManager(db)

    try:
        stakeholders = manager.identify_stakeholders(deal_id)
        probability = manager.predict_close_probability(deal_id)
        health = manager.calculate_deal_health(deal_id)

        return DealIntelligenceResponse(
            deal_id=deal_id,
            stakeholders=[
                StakeholderResponse(
                    person_id=s.person_id,
                    email=s.email,
                    name=s.name,
                    title=s.title,
                    buyer_role=s.buyer_role,
                    influence_level=s.influence_level,
                    engagement_score=s.engagement_score,
                    email_open_count=s.email_open_count,
                    meeting_count=s.meeting_count,
                    last_activity=s.last_activity.isoformat() if s.last_activity else None,
                )
                for s in stakeholders
            ],
            probability=ProbabilityResponse(
                close_probability=probability.close_probability,
                confidence_level=probability.confidence_level,
                probability_low=probability.probability_low,
                probability_high=probability.probability_high,
                model_version=probability.model_version,
            ),
            health=DealHealthResponse(
                health_score=health.health_score,
                health_status=health.health_status,
                engagement_health=health.engagement_health,
                momentum_health=health.momentum_health,
                buyer_health=health.buyer_health,
                competition_health=health.competition_health,
                risk_indicators=health.risk_indicators,
                recommended_actions=health.recommended_actions,
            ),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/deal/{deal_id}/stakeholders")
def get_stakeholders(
    deal_id: str,
    db: Session = Depends(get_db),
):
    """Get buying committee for deal."""
    manager = DealIntelligenceManager(db)
    stakeholders = manager.identify_stakeholders(deal_id)

    return [
        StakeholderResponse(
            person_id=s.person_id,
            email=s.email,
            name=s.name,
            title=s.title,
            buyer_role=s.buyer_role,
            influence_level=s.influence_level,
            engagement_score=s.engagement_score,
            email_open_count=s.email_open_count,
            meeting_count=s.meeting_count,
            last_activity=s.last_activity.isoformat() if s.last_activity else None,
        )
        for s in stakeholders
    ]


@router.post("/deal/{deal_id}/stakeholders")
def add_stakeholder(
    deal_id: str,
    request: AddStakeholderRequest,
    db: Session = Depends(get_db),
):
    """Add stakeholder to buying committee."""
    manager = DealIntelligenceManager(db)

    try:
        stakeholder = manager.add_stakeholder(
            deal_id=deal_id,
            person_id=request.person_id,
            email=request.email,
            name=request.name,
            title=request.title,
            buyer_role=request.buyer_role,
            influence_level=request.influence_level,
        )

        return StakeholderResponse(
            person_id=stakeholder.person_id,
            email=stakeholder.email,
            name=stakeholder.name,
            title=stakeholder.title,
            buyer_role=stakeholder.buyer_role,
            influence_level=stakeholder.influence_level,
            engagement_score=stakeholder.engagement_score,
            email_open_count=stakeholder.email_open_count,
            meeting_count=stakeholder.meeting_count,
            last_activity=stakeholder.last_activity.isoformat() if stakeholder.last_activity else None,
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/deal/{deal_id}/stakeholders/{person_id}/engagement")
def record_engagement(
    deal_id: str,
    person_id: str,
    request: EngagementEventRequest,
    db: Session = Depends(get_db),
):
    """Record engagement event for stakeholder."""
    manager = DealIntelligenceManager(db)

    try:
        manager.update_stakeholder_engagement(
            deal_id=deal_id,
            person_id=person_id,
            event_type=request.event_type,
            event_details=request.event_details,
        )

        return {"success": True, "event_type": request.event_type}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/deal/{deal_id}/probability")
def get_probability(
    deal_id: str,
    db: Session = Depends(get_db),
):
    """Get deal close probability prediction."""
    manager = DealIntelligenceManager(db)

    try:
        result = manager.predict_close_probability(deal_id)

        return ProbabilityResponse(
            close_probability=result.close_probability,
            confidence_level=result.confidence_level,
            probability_low=result.probability_low,
            probability_high=result.probability_high,
            model_version=result.model_version,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/deal/{deal_id}/health")
def get_health(
    deal_id: str,
    db: Session = Depends(get_db),
):
    """Get deal health score and status."""
    manager = DealIntelligenceManager(db)

    try:
        result = manager.calculate_deal_health(deal_id)

        return DealHealthResponse(
            health_score=result.health_score,
            health_status=result.health_status,
            engagement_health=result.engagement_health,
            momentum_health=result.momentum_health,
            buyer_health=result.buyer_health,
            competition_health=result.competition_health,
            risk_indicators=result.risk_indicators,
            recommended_actions=result.recommended_actions,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
