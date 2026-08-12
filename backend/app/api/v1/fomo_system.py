"""FOOM Double-Engine API endpoints.

Routes:
- GET /foom/deal/{deal_id} - Get FOOM status for deal
- GET /foom/platform - Get platform FOOM metrics
- POST /foom/triggers - Generate all FOOM triggers
- POST /foom/cost-of-delay - Calculate delay cost
- POST /foom/social-post - Generate social content
- POST /foom/email-subject - Generate email subject
- POST /foom/video-script - Generate video script
- GET /foom/micro-commitments/{step} - Get next commitment
- POST /foom/competitor-intel - Get competitive data
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.domains.enterprise.fomo_system import (
    ScarcityEngine,
    SocialProofEngine,
    CostOfDelayCalculator,
    LossAversionEngine,
    AuthoritySignalsEngine,
    MicroCommitmentSequence,
    FOOMContentGenerator,
    CompetitiveIntelligenceTracker,
    RealTimeFOMODashboard,
)

router = APIRouter(prefix="/api/v1/foom", tags=["foom-system"])


# ============================================================
# REQUEST/RESPONSE MODELS
# ============================================================


class TriggersRequest(BaseModel):
    deal_id: str
    include_channels: Optional[List[str]] = None  # ["in_app", "social", "personal"]


class TriggersResponse(BaseModel):
    deal_id: str
    foom_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    foom_score: int  # 1-10
    triggers: List[dict]


class CostOfDelayRequest(BaseModel):
    annual_loss: float
    prospect_pain: str


class CostOfDelayResponse(BaseModel):
    daily_cost: float
    monthly_cost: float
    annual_cost: float
    urgency_message: str


class SocialPostRequest(BaseModel):
    deal_id: str
    trigger_type: str
    company_name: str
    industry: str


class SocialPostResponse(BaseModel):
    post: str
    platform: str


class EmailSubjectRequest(BaseModel):
    deal_id: str
    trigger_type: str


class EmailSubjectResponse(BaseModel):
    subject: str
    expected_open_rate: float


class VideoScriptRequest(BaseModel):
    deal_id: str
    trigger_type: str
    duration_seconds: int = 30


class VideoScriptResponse(BaseModel):
    script: str
    duration_seconds: int


class CompetitorIntelRequest(BaseModel):
    industry: str
    days: int = 30


class CompetitorIntelResponse(BaseModel):
    competitor_wins: int
    adoption_rate: int
    market_share_at_risk: float


# ============================================================
# ENDPOINTS
# ============================================================


@router.get("/deal/{deal_id}")
def get_deal_foom_status(deal_id: str, db: Session = Depends(get_db)):
    """Get real-time FOOM status for a deal."""
    try:
        dashboard = RealTimeFOMODashboard(db)
        foom_status = dashboard.get_deal_foom_status(deal_id)

        if not foom_status:
            raise HTTPException(status_code=404, detail="Deal not found")

        return foom_status
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/platform")
def get_platform_foom_metrics(db: Session = Depends(get_db)):
    """Get FOOM metrics for SellIA platform itself."""
    try:
        dashboard = RealTimeFOMODashboard(db)
        metrics = dashboard.get_platform_foom_metrics()
        return metrics
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/triggers", response_model=TriggersResponse)
def generate_all_triggers(request: TriggersRequest, db: Session = Depends(get_db)):
    """Generate all FOOM triggers for deal."""
    try:
        from backend.app.models.deal import Deal

        deal = db.query(Deal).filter(Deal.id == request.deal_id).first()
        if not deal:
            raise HTTPException(status_code=404, detail="Deal not found")

        deal_dict = {
            "id": deal.id,
            "remaining_slots": getattr(deal, "remaining_slots", 10),
            "days_to_price_increase": getattr(deal, "days_to_price_increase", 0),
            "industry": getattr(deal, "industry", "technology"),
            "competitor_wins_this_month": 2,
        }

        # Generate all triggers
        scarcity = ScarcityEngine(db).generate_scarcity_triggers(deal_dict)
        social_proof = SocialProofEngine(db).generate_social_proof_triggers(deal_dict)
        loss_aversion = LossAversionEngine(db).generate_loss_aversion_triggers(deal_dict)
        authority = AuthoritySignalsEngine(db).generate_authority_triggers(deal_dict)

        all_triggers = scarcity + social_proof + loss_aversion + authority

        # Filter by channels if requested
        if request.include_channels:
            all_triggers = [t for t in all_triggers if t.channel in request.include_channels]

        max_urgency = max([t.urgency_level for t in all_triggers]) if all_triggers else 0
        foom_level = "CRITICAL" if max_urgency >= 9 else \
                     "HIGH" if max_urgency >= 7 else \
                     "MEDIUM" if max_urgency >= 5 else \
                     "LOW"

        return TriggersResponse(
            deal_id=request.deal_id,
            foom_level=foom_level,
            foom_score=max_urgency,
            triggers=[
                {
                    "type": t.type,
                    "trigger": t.trigger,
                    "psychology": t.psychology,
                    "urgency": t.urgency_level,
                    "deployment": t.deployment,
                    "channel": t.channel,
                    "duration_minutes": t.duration_minutes,
                }
                for t in all_triggers
            ],
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/cost-of-delay", response_model=CostOfDelayResponse)
def calculate_cost_of_delay(request: CostOfDelayRequest, db: Session = Depends(get_db)):
    """Calculate cost of delaying decision."""
    try:
        calculator = CostOfDelayCalculator(db)
        cost = calculator.calculate_delay_cost({"annual_loss": request.annual_loss})

        return CostOfDelayResponse(
            daily_cost=cost["daily"],
            monthly_cost=cost["monthly"],
            annual_cost=cost["annual"],
            urgency_message=cost["urgency_message"],
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/social-post", response_model=SocialPostResponse)
def generate_social_post(request: SocialPostRequest, db: Session = Depends(get_db)):
    """Generate shareable social media post."""
    try:
        dashboard = RealTimeFOMODashboard(db)
        foom_status = dashboard.get_deal_foom_status(request.deal_id)

        if not foom_status:
            raise HTTPException(status_code=404, detail="Deal not found")

        # Find matching trigger
        trigger_found = None
        for t in foom_status.get("triggers", []):
            if t["type"] == request.trigger_type:
                trigger_found = t
                break

        if not trigger_found:
            raise HTTPException(status_code=400, detail="Trigger type not found")

        # Generate post
        generator = FOOMContentGenerator(db)
        # Create a simple trigger object
        from backend.app.domains.enterprise.fomo_system import FOOMTrigger

        trigger = FOOMTrigger(
            type=trigger_found["type"],
            trigger=trigger_found["trigger"],
            psychology=trigger_found["psychology"],
            urgency_level=trigger_found["urgency"],
            deployment=trigger_found["deployment"],
            channel=trigger_found["channel"],
            duration_minutes=trigger_found.get("duration_minutes", 1440),
        )

        user_context = {
            "company_name": request.company_name,
            "industry": request.industry,
        }

        post = generator.generate_social_post(trigger, user_context)

        return SocialPostResponse(post=post, platform="social")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/email-subject", response_model=EmailSubjectResponse)
def generate_email_subject(request: EmailSubjectRequest, db: Session = Depends(get_db)):
    """Generate high-open-rate email subject."""
    try:
        dashboard = RealTimeFOMODashboard(db)
        foom_status = dashboard.get_deal_foom_status(request.deal_id)

        if not foom_status:
            raise HTTPException(status_code=404, detail="Deal not found")

        # Find matching trigger
        trigger_found = None
        for t in foom_status.get("triggers", []):
            if t["type"] == request.trigger_type:
                trigger_found = t
                break

        if not trigger_found:
            raise HTTPException(status_code=400, detail="Trigger type not found")

        generator = FOOMContentGenerator(db)
        from backend.app.domains.enterprise.fomo_system import FOOMTrigger

        trigger = FOOMTrigger(
            type=trigger_found["type"],
            trigger=trigger_found["trigger"],
            psychology=trigger_found["psychology"],
            urgency_level=trigger_found["urgency"],
            deployment=trigger_found["deployment"],
            channel=trigger_found["channel"],
            duration_minutes=trigger_found.get("duration_minutes", 1440),
        )

        subject = generator.generate_email_subject(trigger)

        return EmailSubjectResponse(subject=subject, expected_open_rate=0.35)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/video-script", response_model=VideoScriptResponse)
def generate_video_script(request: VideoScriptRequest, db: Session = Depends(get_db)):
    """Generate short-form video script."""
    try:
        dashboard = RealTimeFOMODashboard(db)
        foom_status = dashboard.get_deal_foom_status(request.deal_id)

        if not foom_status:
            raise HTTPException(status_code=404, detail="Deal not found")

        trigger_found = None
        for t in foom_status.get("triggers", []):
            if t["type"] == request.trigger_type:
                trigger_found = t
                break

        if not trigger_found:
            raise HTTPException(status_code=400, detail="Trigger type not found")

        generator = FOOMContentGenerator(db)
        from backend.app.domains.enterprise.fomo_system import FOOMTrigger

        trigger = FOOMTrigger(
            type=trigger_found["type"],
            trigger=trigger_found["trigger"],
            psychology=trigger_found["psychology"],
            urgency_level=trigger_found["urgency"],
            deployment=trigger_found["deployment"],
            channel=trigger_found["channel"],
            duration_minutes=trigger_found.get("duration_minutes", 1440),
        )

        script = generator.generate_video_script(trigger, request.duration_seconds)

        return VideoScriptResponse(script=script, duration_seconds=request.duration_seconds)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/micro-commitments/{step}")
def get_micro_commitment(step: int, db: Session = Depends(get_db)):
    """Get next micro-commitment in 7-step sequence."""
    try:
        if step < 1 or step > 7:
            raise HTTPException(status_code=400, detail="Step must be 1-7")

        engine = MicroCommitmentSequence(db)
        commitment = engine.get_micro_commitment(step)

        return {
            "step": step,
            "commitment": commitment["commitment"],
            "psychology": commitment["psychology"],
            "ask": commitment["ask"],
            "if_objection": commitment["ifno"],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/competitor-intel", response_model=CompetitorIntelResponse)
def get_competitor_intelligence(request: CompetitorIntelRequest, db: Session = Depends(get_db)):
    """Get competitive intelligence."""
    try:
        tracker = CompetitiveIntelligenceTracker(db)

        competitor_wins = tracker.get_competitor_wins(request.industry, request.days)
        adoption_rate = tracker.get_industry_adoption_rate("solution", request.industry)
        market_share_trends = tracker.get_market_share_trends("your_company", request.industry)

        return CompetitorIntelResponse(
            competitor_wins=competitor_wins,
            adoption_rate=adoption_rate,
            market_share_at_risk=market_share_trends.get("at_risk_percent", 0),
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
