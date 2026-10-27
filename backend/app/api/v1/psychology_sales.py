"""Phase 31 Psychology Sales API endpoints."""

import uuid
from typing import Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.crm.models import Deal
from app.domains.enterprise.psychology_automations import EVENTS, GOALS, plan_automation
from app.domains.enterprise.psychology_intelligence import (
    DRIVER_LABELS,
    BuyerProfile,
    load_profile,
    plan_moves,
)
from app.domains.enterprise.psychology_sales import (
    AssumptiveCloseEngine,
    DiscoveryQuestionsEngine,
    NeedCreationEngine,
    PsychologyObjectionHandler,
    UrgencyTriggerEngine,
)

router = APIRouter(prefix="/api/v1/psychology", tags=["psychology-sales"])


async def _deal_or_404(db: AsyncSession, deal_id: str) -> Deal:
    """The deal the request talks about. 422 for a malformed id, 404 when it does not exist."""
    try:
        deal_uuid = uuid.UUID(str(deal_id))
    except ValueError:
        raise HTTPException(status_code=422, detail="deal_id must be a UUID")
    deal = (await db.execute(select(Deal).where(Deal.id == deal_uuid))).scalar_one_or_none()
    if deal is None:
        raise HTTPException(status_code=404, detail="Deal not found")
    return deal


# ============================================================
# REQUEST/RESPONSE MODELS
# ============================================================


class BusinessEvidence(BaseModel):
    """Facts the business can back. A move that needs one stays blocked until it is given."""

    customers_same_industry: Optional[int] = Field(None, ge=1, description="Clientes reales del mismo rubro")
    case_result: Optional[str] = Field(None, max_length=300, description="Resultado verificable de un cliente")
    capacity_slots: Optional[int] = Field(None, ge=1, description="Lugares realmente disponibles")
    capacity_reason: Optional[str] = Field(None, max_length=300, description="Por qué hay capacidad limitada")
    price_change_date: Optional[str] = Field(None, max_length=60, description="Fecha en que cambia el precio")
    price_change_detail: Optional[str] = Field(None, max_length=300, description="Qué cambia y cuánto")
    guarantee: Optional[str] = Field(None, max_length=300, description="Garantía que el negocio ofrece")
    free_offer: Optional[str] = Field(None, max_length=300, description="Algo gratis que el negocio puede dar")
    price_summary: Optional[str] = Field(None, max_length=300, description="La inversión, en palabras del negocio")


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
    evidence: Optional[BusinessEvidence] = None


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


class SignalsOut(BaseModel):
    answers: int
    decision_maker: bool
    annual_cost: float
    quotes: Dict[str, str]


class BuyerIntelligenceResponse(BaseModel):
    readiness: int
    stage: str
    driver: str
    driver_label: str
    open_objections: int
    signals: SignalsOut


class NextMovesRequest(BaseModel):
    evidence: Optional[BusinessEvidence] = None


class MoveOut(BaseModel):
    id: str
    kind: str
    principle: str
    why: str
    line: Optional[str]
    missing: List[str]


class NextMovesResponse(BaseModel):
    readiness: int
    stage: str
    driver: str
    driver_label: str
    ready: List[MoveOut]
    blocked: List[MoveOut]


AutomationEvent = Literal[
    "first_contact",
    "new_lead",
    "silent_3_days",
    "objection_price",
    "objection_time",
    "proposal_sent",
    "deal_won",
    "inactive_30_days",
]


class AutomationRequest(BaseModel):
    event: AutomationEvent
    evidence: Optional[BusinessEvidence] = None


class AutomationDraftOut(BaseModel):
    id: str
    goal: str
    principle: str
    text: Optional[str]
    missing: List[str]


class AutomationResponse(BaseModel):
    event: str
    event_label: str
    ready: List[AutomationDraftOut]
    blocked: List[AutomationDraftOut]
    drafts_need_approval: bool = True


class AutomationCatalogResponse(BaseModel):
    goals: Dict[str, str]
    events: Dict[str, str]


# ============================================================
# ENDPOINTS
# ============================================================


@router.post("/discovery-questions", response_model=DiscoveryQuestionResponse)
async def get_discovery_questions(
    request: DiscoveryQuestionRequest,
    db: AsyncSession = Depends(get_db),
):
    """Get contextual discovery questions for prospect."""

    try:
        deal = await _deal_or_404(db, request.deal_id)

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
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/record-response", response_model=RecordResponseResponse)
async def record_discovery_response(
    request: RecordResponseRequest,
    db: AsyncSession = Depends(get_db),
):
    """Record prospect's response to discovery question."""

    try:
        await _deal_or_404(db, request.deal_id)
        engine = DiscoveryQuestionsEngine(db)
        db_response = await engine.record_response(request.deal_id, request.question, request.response)

        return RecordResponseResponse(
            recorded=True,
            urgency_level=db_response.urgency_level or 5,
            pain_points=db_response.pain_points or [],
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/create-need-narrative", response_model=NeedNarrativeResponse)
async def create_need_narrative(
    request: NeedNarrativeRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create need narrative from discovery responses."""

    try:
        await _deal_or_404(db, request.deal_id)
        engine = NeedCreationEngine(db)
        result = await engine.create_need_narrative(request.deal_id, request.discovery_responses)

        return NeedNarrativeResponse(
            narrative=result.narrative,
            financial_impact=result.financial_impact,
            urgency_level=result.urgency_level,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/urgency-triggers", response_model=UrgencyTriggersResponse)
def get_urgency_triggers(
    request: UrgencyTriggersRequest,
    db: AsyncSession = Depends(get_db),
):
    """Urgency lines the business can back with its own facts. Without facts the list is empty."""

    try:
        evidence = request.evidence.model_dump(exclude_none=True) if request.evidence else {}

        engine = UrgencyTriggerEngine(db)
        triggers = engine.generate_urgency_triggers(evidence)

        return UrgencyTriggersResponse(triggers=triggers)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/handle-objection", response_model=ObjectionResponse)
def handle_objection(
    request: ObjectionRequest,
    db: AsyncSession = Depends(get_db),
):
    """Get psychology-based objection response."""

    try:
        prospect = {"role": request.prospect_role}

        handler = PsychologyObjectionHandler(db)
        response = handler.handle_objection(request.objection, prospect)

        return ObjectionResponse(
            response=response,
            psychology="Validar → Reencuadrar → Preguntar",
            next_step="Pedirle que piense en el impacto",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/close", response_model=CloseResponse)
def get_close(
    request: CloseRequest,
    db: AsyncSession = Depends(get_db),
):
    """Get assumptive close for current step."""

    try:
        engine = AssumptiveCloseEngine(db)

        # Analyze their response
        is_positive = engine._is_positive_response(request.prospect_response)

        if not is_positive:
            # Handle objection, stay on step
            return CloseResponse(
                next_close="Te entiendo totalmente. Déjame preguntarte esto…",
                step=request.current_step,
                psychology="Validar la objeción",
                is_positive_response=False,
            )

        # Move to next step
        next_step = request.current_step + 1
        next_close = engine.get_close(next_step)

        return CloseResponse(
            next_close=next_close,
            step=next_step,
            psychology="Avanzar con compromisos pequeños",
            is_positive_response=True,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


def _intelligence_out(profile: BuyerProfile) -> BuyerIntelligenceResponse:
    return BuyerIntelligenceResponse(
        readiness=profile.readiness,
        stage=profile.stage,
        driver=profile.driver,
        driver_label=DRIVER_LABELS[profile.driver],
        open_objections=profile.open_objections,
        signals=SignalsOut(
            answers=profile.signals.answers,
            decision_maker=profile.signals.decision_maker,
            annual_cost=profile.signals.annual_cost,
            quotes=profile.signals.quotes,
        ),
    )


@router.get("/deals/{deal_id}/intelligence", response_model=BuyerIntelligenceResponse)
async def get_buyer_intelligence(
    deal_id: str,
    db: AsyncSession = Depends(get_db),
):
    """How ready the prospect is and which lever fits, read from what they actually said."""

    await _deal_or_404(db, deal_id)
    profile = await load_profile(db, deal_id)
    return _intelligence_out(profile)


@router.post("/deals/{deal_id}/next-moves", response_model=NextMovesResponse)
async def get_next_moves(
    deal_id: str,
    request: NextMovesRequest,
    db: AsyncSession = Depends(get_db),
):
    """Persuasion and urgency moves that fit this prospect now.

    Moves that need a business fact the request did not supply are returned as blocked, with the
    facts missing. Nothing is filled in with an invented claim.
    """

    await _deal_or_404(db, deal_id)
    profile = await load_profile(db, deal_id)
    evidence = request.evidence.model_dump(exclude_none=True) if request.evidence else {}
    plan = plan_moves(profile, evidence)

    def to_out(move) -> MoveOut:
        return MoveOut(
            id=move.id,
            kind=move.kind,
            principle=move.principle,
            why=move.why,
            line=move.line,
            missing=list(move.missing),
        )

    return NextMovesResponse(
        readiness=profile.readiness,
        stage=profile.stage,
        driver=profile.driver,
        driver_label=DRIVER_LABELS[profile.driver],
        ready=[to_out(m) for m in plan.ready],
        blocked=[to_out(m) for m in plan.blocked],
    )


@router.get("/automation/catalog", response_model=AutomationCatalogResponse)
def get_automation_catalog():
    """The goals (captar, confianza, cerrar, fidelizar) and the events the automations respond to."""

    return AutomationCatalogResponse(goals=GOALS, events=EVENTS)


@router.post("/deals/{deal_id}/automation", response_model=AutomationResponse)
async def get_automation_response(
    deal_id: str,
    request: AutomationRequest,
    db: AsyncSession = Depends(get_db),
):
    """Psychological response for one event on this deal, as drafts. Sending is a separate, approved step.

    Drafts that need a business fact the request did not give come back as blocked, with the fact missing.
    """

    await _deal_or_404(db, deal_id)
    profile = await load_profile(db, deal_id)
    evidence = request.evidence.model_dump(exclude_none=True) if request.evidence else {}
    plan = plan_automation(request.event, profile, evidence)

    def to_out(draft) -> AutomationDraftOut:
        return AutomationDraftOut(
            id=draft.id,
            goal=GOALS[draft.goal],
            principle=draft.principle,
            text=draft.text,
            missing=list(draft.missing),
        )

    return AutomationResponse(
        event=request.event,
        event_label=EVENTS[request.event],
        ready=[to_out(d) for d in plan.ready],
        blocked=[to_out(d) for d in plan.blocked],
    )
