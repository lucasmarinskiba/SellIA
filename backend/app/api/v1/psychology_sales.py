"""Phase 31 Psychology Sales API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.domains.enterprise.psychology_sales import (
    DiscoveryQuestionsEngine,
    NeedCreationEngine,
    UrgencyTriggerEngine,
    PsychologyObjectionHandler,
    AssumptiveCloseEngine,
)

router = APIRouter(prefix="/api/v1/psychology", tags=["psychology-sales"])


# ============================================================
# REQUEST/RESPONSE MODELS
# ============================================================


class DiscoveryQuestionRequest(BaseModel):
    prospect_id: str
    deal_id: str
    stage: str


class DiscoveryQuestionResponse(BaseModel):
    questions: List[str]
    psychology: List[str]
    next_stage: str


class RecordResponseRequest(BaseModel):
    deal_id: str
    question: str
    response: str


class RecordResponseResponse(BaseModel):
    recorded: bool
    urgency_level: int
    pain_points: List[str]


class NeedNarrativeRequest(BaseModel):
    deal_id: str
    discovery_responses: List[str]


class NeedNarrativeResponse(BaseModel):
    narrative: str
    financial_impact: float
    urgency_level: float


class UrgencyTriggersRequest(BaseModel):
    deal_id: str
    stage: str
    industry: str


class UrgencyTriggersResponse(BaseModel):
    triggers: List[dict]


class ObjectionRequest(BaseModel):
    deal_id: str
    objection: str
    prospect_role: str


class ObjectionResponse(BaseModel):
    response: str
    psychology: str
    next_step: str


class CloseRequest(BaseModel):
    deal_id: str
    current_step: int
    prospect_response: str


class CloseResponse(BaseModel):
    next_close: str
    step: int
    psychology: str
    is_positive_response: bool


# ============================================================
# ENDPOINTS
# ============================================================


@router.post("/discovery-questions", response_model=DiscoveryQuestionResponse)
def get_discovery_questions(
    request: DiscoveryQuestionRequest,
    db: Session = Depends(get_db),
):
    """Get contextual discovery questions for prospect."""

    try:
        from backend.app.models.deal import Deal

        deal = db.query(Deal).filter(Deal.id == request.deal_id).first()
        if not deal:
            raise HTTPException(status_code=404, detail="Deal not found")

        prospect = {
            "company_name": deal.company_name if hasattr(deal, 'company_name') else "Company",
            "industry": getattr(deal, "industry", "technology"),
            "role": "decision_maker",
        }

        engine = DiscoveryQuestionsEngine(db)
        questions = engine.generate_questions(prospect, request.stage)

        return DiscoveryQuestionResponse(
            questions=[q.question for q in questions],
            psychology=[q.psychology for q in questions],
            next_stage=request.stage,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/record-response", response_model=RecordResponseResponse)
def record_discovery_response(
    request: RecordResponseRequest,
    db: Session = Depends(get_db),
):
    """Record prospect's response to discovery question."""

    try:
        engine = DiscoveryQuestionsEngine(db)
        db_response = engine.record_response(request.deal_id, request.question, request.response)

        return RecordResponseResponse(
            recorded=True,
            urgency_level=db_response.urgency_level or 5,
            pain_points=db_response.pain_points or [],
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/create-need-narrative", response_model=NeedNarrativeResponse)
def create_need_narrative(
    request: NeedNarrativeRequest,
    db: Session = Depends(get_db),
):
    """Create need narrative from discovery responses."""

    try:
        engine = NeedCreationEngine(db)
        result = engine.create_need_narrative(request.deal_id, request.discovery_responses)

        return NeedNarrativeResponse(
            narrative=result.narrative,
            financial_impact=result.financial_impact,
            urgency_level=result.urgency_level,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/urgency-triggers", response_model=UrgencyTriggersResponse)
def get_urgency_triggers(
    request: UrgencyTriggersRequest,
    db: Session = Depends(get_db),
):
    """Get FOMO/urgency triggers for deal."""

    try:
        deal = {"stage": request.stage, "industry": request.industry}

        engine = UrgencyTriggerEngine(db)
        triggers = engine.generate_urgency_triggers(deal)

        return UrgencyTriggersResponse(triggers=triggers)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/handle-objection", response_model=ObjectionResponse)
def handle_objection(
    request: ObjectionRequest,
    db: Session = Depends(get_db),
):
    """Get psychology-based objection response."""

    try:
        prospect = {"role": request.prospect_role}

        handler = PsychologyObjectionHandler(db)
        response = handler.handle_objection(request.objection, prospect)

        return ObjectionResponse(
            response=response,
            psychology="Validate → Reframe → Question",
            next_step="Ask them to think about impact",
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/close", response_model=CloseResponse)
def get_close(
    request: CloseRequest,
    db: Session = Depends(get_db),
):
    """Get assumptive close for current step."""

    try:
        engine = AssumptiveCloseEngine(db)

        # Analyze their response
        is_positive = engine._is_positive_response(request.prospect_response)

        if not is_positive:
            # Handle objection, stay on step
            return CloseResponse(
                next_close="I totally understand. Let me ask you this...",
                step=request.current_step,
                psychology="Validate objection",
                is_positive_response=False,
            )

        # Move to next step
        next_step = request.current_step + 1
        next_close = engine.get_close(next_step)

        return CloseResponse(
            next_close=next_close,
            step=next_step,
            psychology="Build momentum with small commitments",
            is_positive_response=True,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
