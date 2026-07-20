"""Lead Qualifier Auto-Agent Service"""

import uuid
import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.logger import get_logger
from app.domains.agents.lead_qualifier.models import LeadQualification
from app.domains.agents.lead_qualifier.schemas import BANTScore
from app.domains.channels.models import Conversation, Message
from app.domains.agents.ai_reply import generate_raw_ai_response
from app.domains.agents.prompts.business_context_adapter import (
    get_agent_prompt_context,
    format_business_context_for_prompt,
)

logger = get_logger(__name__)

BANT_WEIGHTS = {
    "budget": 0.25,
    "authority": 0.25,
    "need": 0.30,
    "timeline": 0.20,
}

BANT_QUESTIONS = {
    "budget": "¿Cuál es el presupuesto que tienes destinado para esta solución?",
    "authority": "¿Eres la persona que toma la decisión final o necesitas consultar con alguien más?",
    "need": "¿Qué problema necesitas resolver urgentemente?",
    "timeline": "¿En qué plazo necesitas tener la solución implementada?",
}


async def qualify_lead(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    business_id: uuid.UUID,
    customer_id: Optional[uuid.UUID] = None,
) -> Dict[str, Any]:
    """
    1. Analyzes conversation history
    2. Extracts BANT via LLM
    3. Calculates weighted qualification score
    4. Routes based on score
    5. Generates qualification summary
    """
    # Load conversation messages
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
    )
    messages = result.scalars().all()
    conversation_text = "\n".join(
        f"{'Cliente' if m.direction.value == 'inbound' else 'Vendedor'}: {m.content}"
        for m in messages
    )

    # Extract BANT via LLM
    ctx = await get_agent_prompt_context(db, business_id)
    context_block = format_business_context_for_prompt(ctx)

    system_prompt = (
        "Eres un experto en calificación de leads BANT. "
        "Analiza la conversación y devuelve SOLO un JSON válido con esta estructura exacta:\n"
        '{\n'
        '  "budget": {"score": 0-100, "reasoning": "..."},\n'
        '  "authority": {"score": 0-100, "reasoning": "..."},\n'
        '  "need": {"score": 0-100, "reasoning": "..."},\n'
        '  "timeline": {"score": 0-100, "reasoning": "..."}\n'
        '}\n'
        "Reglas:\n"
        "- budget: 100 = presupuesto claro y suficiente, 0 = sin presupuesto o muy bajo.\n"
        "- authority: 100 = decisor final, 0 = sin influencia.\n"
        "- need: 100 = necesidad crítica y bien definida, 0 = sin necesidad.\n"
        "- timeline: 100 = quiere comprar ya, 0 = sin urgencia.\n"
    )
    user_prompt = f"Conversación:\n{conversation_text[:4000]}\n\nJSON BANT:"
    if context_block:
        user_prompt = f"{context_block}\n\n{user_prompt}"

    raw = await generate_raw_ai_response(
        db=db,
        business_id=business_id,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        max_tokens=800,
        temperature=0.3,
    )

    bant = {"budget": 0, "authority": 0, "need": 0, "timeline": 0}
    if raw:
        try:
            json_str = raw.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()
            parsed = json.loads(json_str)
            for dim in bant:
                val = parsed.get(dim, {})
                if isinstance(val, dict):
                    bant[dim] = int(val.get("score", 0))
                else:
                    bant[dim] = int(val)
        except Exception as e:
            logger.warning(f"Failed to parse BANT JSON: {e}")

    bant_score = BANTScore(**bant)
    qualification_score = sum(
        getattr(bant_score, dim) * weight for dim, weight in BANT_WEIGHTS.items()
    )

    # Routing
    if qualification_score >= 70:
        status = "qualified"
        routing_destination = "sales_team"
    elif qualification_score >= 40:
        status = "nurture"
        routing_destination = "drip_sequence"
    else:
        status = "disqualified"
        routing_destination = None

    # Generate summary
    summary = await _generate_qualification_summary(
        db, business_id, bant_score, qualification_score, status
    )

    # Persist
    qualification = LeadQualification(
        business_id=business_id,
        conversation_id=conversation_id,
        customer_id=customer_id,
        bant_score=bant.model_dump(),
        qualification_score=qualification_score,
        status=status,
        routing_destination=routing_destination,
        summary=summary,
    )
    db.add(qualification)
    await db.commit()
    await db.refresh(qualification)

    # Suggest next question
    next_question = await ask_qualifying_question(db, conversation_id, bant_score)

    return {
        "qualification_id": qualification.id,
        "bant_score": bant_score,
        "qualification_score": qualification_score,
        "status": status,
        "routing_destination": routing_destination,
        "summary": summary,
        "next_question": next_question,
    }


async def _generate_qualification_summary(
    db: AsyncSession,
    business_id: uuid.UUID,
    bant_score: BANTScore,
    qualification_score: float,
    status: str,
) -> str:
    """Generate a human-readable summary of the qualification."""
    ctx = await get_agent_prompt_context(db, business_id)
    context_block = format_business_context_for_prompt(ctx)

    system_prompt = (
        "Eres un experto en ventas. Resume la calificación de un lead en 2-3 oraciones en español. "
        "Sé directo y profesional."
    )
    user_prompt = (
        f"Puntuación BANT:\n"
        f"- Presupuesto: {bant_score.budget}/100\n"
        f"- Autoridad: {bant_score.authority}/100\n"
        f"- Necesidad: {bant_score.need}/100\n"
        f"- Plazo: {bant_score.timeline}/100\n"
        f"Puntuación total: {qualification_score:.0f}/100\n"
        f"Estado: {status}\n\n"
        "Resumen:"
    )
    if context_block:
        user_prompt = f"{context_block}\n\n{user_prompt}"
    summary = await generate_raw_ai_response(
        db=db,
        business_id=business_id,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        max_tokens=200,
        temperature=0.5,
    )
    return summary or "Lead calificado."


async def ask_qualifying_question(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    bant_score: Optional[BANTScore] = None,
) -> str:
    """Suggests the next BANT question to ask based on missing dimensions."""
    if bant_score is None:
        # Try to load existing qualification
        result = await db.execute(
            select(LeadQualification)
            .where(LeadQualification.conversation_id == conversation_id)
            .order_by(desc(LeadQualification.created_at))
        )
        qual = result.scalar_one_or_none()
        if qual and qual.bant_score:
            bant_score = BANTScore(**qual.bant_score)
        else:
            bant_score = BANTScore(budget=0, authority=0, need=0, timeline=0)

    scores = {
        "budget": bant_score.budget,
        "authority": bant_score.authority,
        "need": bant_score.need,
        "timeline": bant_score.timeline,
    }
    lowest = min(scores, key=scores.get)
    return BANT_QUESTIONS[lowest]


async def get_qualified_leads(
    db: AsyncSession,
    business_id: uuid.UUID,
    min_score: float = 70.0,
    limit: int = 100,
) -> List[LeadQualification]:
    result = await db.execute(
        select(LeadQualification)
        .where(
            LeadQualification.business_id == business_id,
            LeadQualification.qualification_score >= min_score,
        )
        .order_by(desc(LeadQualification.qualification_score))
        .limit(limit)
    )
    return result.scalars().all()


async def get_qualification(db: AsyncSession, qualification_id: uuid.UUID) -> Optional[LeadQualification]:
    result = await db.execute(
        select(LeadQualification).where(LeadQualification.id == qualification_id)
    )
    return result.scalar_one_or_none()


async def route_lead(
    db: AsyncSession,
    qualification_id: uuid.UUID,
    routing_destination: str,
) -> LeadQualification:
    qualification = await get_qualification(db, qualification_id)
    if not qualification:
        raise ValueError("Qualification not found")
    qualification.routing_destination = routing_destination
    if routing_destination == "sales_team":
        qualification.status = "qualified"
    elif routing_destination == "drip_sequence":
        qualification.status = "nurture"
    await db.commit()
    await db.refresh(qualification)
    return qualification
