"""CRM API Router"""

from uuid import UUID
from typing import Optional

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.domains.users.models import User
from app.domains.crm.models import Pipeline, Deal, LeadScore, LeadStage
from app.domains.crm.schemas import (
    PipelineCreate, PipelineUpdate, PipelineResponse,
    DealCreate, DealUpdate, DealResponse, MoveDealRequest,
    LeadScoreResponse, CRMSummaryResponse,
)
from app.domains.channels.models import Conversation, Message

router = APIRouter(prefix="/crm", tags=["crm"])


# ========== Pipelines ==========

@router.get("/pipelines", response_model=list[PipelineResponse])
async def list_pipelines(
    business_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(Pipeline).where(
            Pipeline.business_id == business_id,
            Pipeline.is_active == True,
        ).order_by(Pipeline.is_default.desc(), Pipeline.created_at)
    )
    return result.scalars().all()


@router.post("/pipelines", response_model=PipelineResponse, status_code=status.HTTP_201_CREATED)
async def create_pipeline(
    data: PipelineCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    pipeline = Pipeline(**data.model_dump())
    db.add(pipeline)
    await db.commit()
    await db.refresh(pipeline)
    return pipeline


@router.patch("/pipelines/{pipeline_id}", response_model=PipelineResponse)
async def update_pipeline(
    pipeline_id: UUID,
    data: PipelineUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(Pipeline).where(Pipeline.id == pipeline_id))
    pipeline = result.scalar_one_or_none()
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline no encontrado")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(pipeline, field, value)
    await db.commit()
    await db.refresh(pipeline)
    return pipeline


@router.delete("/pipelines/{pipeline_id}")
async def delete_pipeline(
    pipeline_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(Pipeline).where(Pipeline.id == pipeline_id))
    pipeline = result.scalar_one_or_none()
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline no encontrado")
    pipeline.is_active = False
    await db.commit()
    return {"message": "Pipeline eliminado"}


# ========== Deals ==========

@router.get("/deals", response_model=list[DealResponse])
async def list_deals(
    business_id: UUID = Query(...),
    stage: Optional[str] = None,
    pipeline_id: Optional[UUID] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    query = select(Deal).where(
        Deal.business_id == business_id,
        Deal.is_active == True,
    )
    if stage:
        query = query.where(Deal.stage == stage)
    if pipeline_id:
        query = query.where(Deal.pipeline_id == pipeline_id)
    if search:
        query = query.where(
            Deal.title.ilike(f"%{search}%") | Deal.contact_name.ilike(f"%{search}%")
        )
    result = await db.execute(query.order_by(desc(Deal.priority), desc(Deal.updated_at)))
    return result.scalars().all()


@router.post("/deals", response_model=DealResponse, status_code=status.HTTP_201_CREATED)
async def create_deal(
    data: DealCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    deal_data = data.model_dump()

    # Auto-generate title/description from conversation if not provided
    if data.conversation_id and (not data.title or not data.description):
        try:
            from app.domains.channels.models import Conversation, Message
            from app.domains.agents.ai_reply import generate_ai_response

            result = await db.execute(
                select(Conversation).where(Conversation.id == data.conversation_id)
            )
            conversation = result.scalar_one_or_none()
            if conversation:
                # Get last messages for context
                result = await db.execute(
                    select(Message).where(
                        Message.conversation_id == conversation.id
                    ).order_by(Message.created_at.desc()).limit(10)
                )
                messages = list(reversed(result.scalars().all()))
                conversation_summary = "\n".join([
                    f"{'Lead' if m.direction.value == 'inbound' else 'Agent'}: {m.content[:200]}"
                    for m in messages
                ])

                custom_prompt = f"""Based on this conversation summary, write:
1. A concise deal title (max 8 words) describing the opportunity
2. A brief deal description (2-3 sentences) summarizing the lead's interest and next steps

Conversation:
{conversation_summary}

Format your response exactly as:
TITLE: <deal title>
DESCRIPTION: <deal description>"""

                ai_response = await generate_ai_response(
                    db=db,
                    conversation=conversation,
                    personality_slug="account-executive",
                    business_id=data.business_id,
                    custom_prompt=custom_prompt,
                    max_tokens=300,
                )

                if ai_response:
                    # Parse TITLE and DESCRIPTION from response
                    title_match = None
                    desc_match = None
                    for line in ai_response.split("\n"):
                        if line.upper().startswith("TITLE:"):
                            title_match = line.split(":", 1)[1].strip()
                        elif line.upper().startswith("DESCRIPTION:"):
                            desc_match = line.split(":", 1)[1].strip()

                    if title_match and not data.title:
                        deal_data["title"] = title_match
                    if desc_match and not data.description:
                        deal_data["description"] = desc_match
        except Exception as e:
            from app.core.logger import get_logger
            get_logger(__name__).error(f"Deal AI generation error: {e}")

    deal = Deal(**deal_data)
    db.add(deal)
    await db.commit()
    await db.refresh(deal)
    return deal


async def _generate_close_reason_if_missing(db, deal, business_id):
    """Auto-generate close reason using AI if deal is closed and no reason provided."""
    if deal.close_reason:
        return
    if not deal.conversation_id:
        return

    try:
        from app.domains.agents.ai_reply import generate_ai_response

        result = await db.execute(
            select(Conversation).where(Conversation.id == deal.conversation_id)
        )
        conversation = result.scalar_one_or_none()
        if not conversation:
            return

        result = await db.execute(
            select(Message).where(
                Message.conversation_id == conversation.id
            ).order_by(Message.created_at.desc()).limit(15)
        )
        messages = list(reversed(result.scalars().all()))
        conversation_summary = "\n".join([
            f"{'Lead' if m.direction.value == 'inbound' else 'Agent'}: {m.content[:250]}"
            for m in messages
        ])

        outcome = "GANADO" if deal.stage == LeadStage.CLOSED_WON else "PERDIDO"
        custom_prompt = f"""Analiza esta conversación y genera un brief de cierre profesional.

RESULTADO: Deal {outcome}
VALOR: ${deal.value} {deal.currency}
CONTACTO: {deal.contact_name or 'N/A'}

HISTORIAL DE CONVERSACIÓN:
{conversation_summary}

Genera UNA SOLA ORACIÓN que explique por qué se cerró este deal. Sé objetivo, profesional y accionable. Si se perdió, indica la razón principal."""

        ai_response = await generate_ai_response(
            db=db,
            conversation=conversation,
            personality_slug="data-analyst",
            business_id=business_id,
            custom_prompt=custom_prompt,
            voice_slug="hormozi",
            max_tokens=200,
        )

        if ai_response:
            deal.close_reason = ai_response.strip()
            await db.commit()
    except Exception as e:
        from app.core.logger import get_logger
        get_logger(__name__).error(f"Close reason generation error: {e}")


@router.patch("/deals/{deal_id}", response_model=DealResponse)
async def update_deal(
    deal_id: UUID,
    data: DealUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(Deal).where(Deal.id == deal_id))
    deal = result.scalar_one_or_none()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal no encontrado")

    update_data = data.model_dump(exclude_unset=True)

    # If stage changed to closed, set actual_close_date and generate close reason
    if "stage" in update_data:
        new_stage = update_data["stage"]
        if new_stage in (LeadStage.CLOSED_WON.value, LeadStage.CLOSED_LOST.value):
            update_data["actual_close_date"] = datetime.now(timezone.utc)

    for field, value in update_data.items():
        setattr(deal, field, value)
    await db.commit()

    # Auto-generate close reason if deal is now closed and lacks one
    if deal.stage in (LeadStage.CLOSED_WON, LeadStage.CLOSED_LOST) and not deal.close_reason:
        await _generate_close_reason_if_missing(db, deal, deal.business_id)
        await db.refresh(deal)

    await db.refresh(deal)
    return deal


@router.post("/deals/{deal_id}/move", response_model=DealResponse)
async def move_deal(
    deal_id: UUID,
    data: MoveDealRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(Deal).where(Deal.id == deal_id))
    deal = result.scalar_one_or_none()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal no encontrado")

    deal.stage = data.stage
    if data.order is not None:
        deal.stage_order = data.order

    if data.stage in (LeadStage.CLOSED_WON.value, LeadStage.CLOSED_LOST.value):
        deal.actual_close_date = datetime.now(timezone.utc)

    await db.commit()

    # Auto-generate close reason if deal is now closed and lacks one
    if deal.stage in (LeadStage.CLOSED_WON, LeadStage.CLOSED_LOST) and not deal.close_reason:
        await _generate_close_reason_if_missing(db, deal, deal.business_id)
        await db.refresh(deal)

    # Auto-generate proposal when reaching PROPOSAL_SENT
    if data.stage == LeadStage.PROPOSAL_SENT.value and not deal.extra_data.get("proposal"):
        try:
            from app.domains.crm.proposals import generate_deal_proposal
            await generate_deal_proposal(db, deal, deal.business_id)
            await db.refresh(deal)
        except Exception as e:
            from app.core.logger import get_logger
            get_logger(__name__).error(f"Auto-proposal generation error: {e}")

    await db.refresh(deal)
    return deal


@router.post("/deals/{deal_id}/generate-proposal", response_model=DealResponse)
async def generate_proposal_endpoint(
    deal_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Generate an AI-powered proposal for a deal."""
    result = await db.execute(select(Deal).where(Deal.id == deal_id))
    deal = result.scalar_one_or_none()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal no encontrado")

    from app.domains.crm.proposals import generate_deal_proposal

    proposal = await generate_deal_proposal(db, deal, deal.business_id)
    if not proposal:
        raise HTTPException(status_code=500, detail="No se pudo generar la propuesta")

    await db.commit()
    await db.refresh(deal)
    return deal


@router.post("/deals/{deal_id}/pricing-recommendation", response_model=DealResponse)
async def pricing_recommendation_endpoint(
    deal_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Generate a pricing strategy recommendation for a deal."""
    result = await db.execute(select(Deal).where(Deal.id == deal_id))
    deal = result.scalar_one_or_none()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal no encontrado")

    from app.domains.crm.pricing import generate_pricing_recommendation

    recommendation = await generate_pricing_recommendation(db, deal, deal.business_id)
    if not recommendation:
        raise HTTPException(status_code=500, detail="No se pudo generar la recomendación de precios")

    await db.commit()
    await db.refresh(deal)
    return deal


@router.post("/deals/{deal_id}/assign-recommendation")
async def assign_recommendation_endpoint(
    deal_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get AI-powered deal assignment and handling strategy recommendation."""
    result = await db.execute(select(Deal).where(Deal.id == deal_id))
    deal = result.scalar_one_or_none()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal no encontrado")

    conversation_summary = "Sin conversación disponible."
    if deal.conversation_id:
        msg_result = await db.execute(
            select(Message).where(
                Message.conversation_id == deal.conversation_id
            ).order_by(Message.created_at.desc()).limit(10)
        )
        messages = list(reversed(msg_result.scalars().all()))
        conversation_summary = "\n".join([
            f"{'Lead' if m.direction.value == 'inbound' else 'Agent'}: {m.content[:200]}"
            for m in messages
        ])

    from app.domains.agents.ai_reply import generate_raw_ai_response
    from app.domains.agents.prompts import compose_system_prompt

    system_prompt = compose_system_prompt(base_slug="sales-manager", voice_slug="hormozi")
    user_prompt = f"""Recomienda una estrategia de asignación y manejo para este deal.

DEAL: {deal.title}
DESCRIPCIÓN: {deal.description or 'N/A'}
VALOR: ${deal.value} {deal.currency}
ETAPA: {deal.stage.value if deal.stage else 'N/A'}
CONTACTO: {deal.contact_name or 'N/A'} ({deal.contact_email or 'Sin email'})

CONVERSACIÓN RECIENTE:
{conversation_summary}

Responde con este formato exacto:
ASSIGNMENT_STRATEGY: <cómo manejar este deal: solo IA, handoff humano, o híbrido>
PRIORITY_REASON: <por qué tiene esta prioridad>
NEXT_ACTION: <próxima acción concreta>
ESTIMATED_CLOSE: <estimación de días para cerrar>"""

    ai_response = await generate_raw_ai_response(
        db=db,
        business_id=deal.business_id,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        max_tokens=400,
        temperature=0.6,
    )

    if not ai_response:
        raise HTTPException(status_code=500, detail="No se pudo generar la recomendación")

    # Parse and store
    recommendation = {
        "assignment_strategy": "",
        "priority_reason": "",
        "next_action": "",
        "estimated_close": "",
        "raw": ai_response,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    current_key = None
    key_map = {
        "ASSIGNMENT_STRATEGY": "assignment_strategy",
        "PRIORITY_REASON": "priority_reason",
        "NEXT_ACTION": "next_action",
        "ESTIMATED_CLOSE": "estimated_close",
    }

    for line in ai_response.split("\n"):
        stripped = line.strip()
        matched = False
        for prefix, key in key_map.items():
            if stripped.upper().startswith(f"{prefix}:"):
                current_key = key
                recommendation[key] = stripped.split(":", 1)[1].strip()
                matched = True
                break
        if not matched and current_key and stripped:
            recommendation[current_key] += " " + stripped

    if not deal.extra_data:
        deal.extra_data = {}
    deal.extra_data["assignment_recommendation"] = recommendation
    await db.commit()

    return {"recommendation": recommendation, "deal_id": deal_id}


@router.delete("/deals/{deal_id}")
async def delete_deal(
    deal_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(Deal).where(Deal.id == deal_id))
    deal = result.scalar_one_or_none()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal no encontrado")
    deal.is_active = False
    await db.commit()
    return {"message": "Deal eliminado"}


# ========== Lead Scores ==========

@router.get("/lead-scores", response_model=list[LeadScoreResponse])
async def list_lead_scores(
    business_id: UUID = Query(...),
    classification: Optional[str] = None,
    min_score: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    query = select(LeadScore).where(LeadScore.business_id == business_id)
    if classification:
        query = query.where(LeadScore.classification == classification)
    if min_score:
        query = query.where(LeadScore.total_score >= min_score)
    result = await db.execute(query.order_by(desc(LeadScore.total_score)))
    return result.scalars().all()


@router.get("/lead-scores/{conversation_id}", response_model=LeadScoreResponse)
async def get_lead_score(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(LeadScore).where(LeadScore.conversation_id == conversation_id)
    )
    score = result.scalar_one_or_none()
    if not score:
        raise HTTPException(status_code=404, detail="Lead score no encontrado")
    return score


# ========== Summary ==========

@router.get("/summary", response_model=CRMSummaryResponse)
async def get_crm_summary(
    business_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    # Deals stats
    deals_result = await db.execute(
        select(Deal.stage, func.count(Deal.id), func.coalesce(func.sum(Deal.value), 0))
        .where(Deal.business_id == business_id, Deal.is_active == True)
        .group_by(Deal.stage)
    )
    deals_by_stage = {}
    value_by_stage = {}
    total_deals = 0
    total_value = 0.0
    for row in deals_result.all():
        deals_by_stage[row[0]] = row[1]
        value_by_stage[row[0]] = float(row[2])
        total_deals += row[1]
        total_value += float(row[2])

    # Win rate
    won = deals_by_stage.get(LeadStage.CLOSED_WON.value, 0)
    lost = deals_by_stage.get(LeadStage.CLOSED_LOST.value, 0)
    win_rate = (won / (won + lost) * 100) if (won + lost) > 0 else 0.0

    avg_deal_value = (total_value / total_deals) if total_deals > 0 else 0.0

    # Lead classifications
    hot = await db.execute(select(func.count(LeadScore.id)).where(LeadScore.business_id == business_id, LeadScore.classification == "hot"))
    warm = await db.execute(select(func.count(LeadScore.id)).where(LeadScore.business_id == business_id, LeadScore.classification == "warm"))
    cold = await db.execute(select(func.count(LeadScore.id)).where(LeadScore.business_id == business_id, LeadScore.classification == "cold"))

    return CRMSummaryResponse(
        total_deals=total_deals,
        total_value=total_value,
        deals_by_stage=deals_by_stage,
        value_by_stage=value_by_stage,
        avg_deal_value=avg_deal_value,
        win_rate=win_rate,
        hot_leads=hot.scalar() or 0,
        warm_leads=warm.scalar() or 0,
        cold_leads=cold.scalar() or 0,
    )
