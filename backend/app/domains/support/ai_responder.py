"""
AI Support Responder

Genera respuestas automáticas para tickets de soporte basándose en FAQ y Knowledge Base.
Si la confianza es baja, sugiere escalar a humano.
"""

import uuid
from typing import Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.support.service import SupportService
from app.domains.support.kb_search import search_kb_and_faq
from app.domains.agents.ai_reply import generate_raw_ai_response


CONFIDENCE_THRESHOLD = 0.75
MAX_AI_MESSAGES_BEFORE_ESCALATE = 2


async def generate_ai_response(
    db: AsyncSession,
    business_id: uuid.UUID,
    ticket_title: str,
    ticket_description: str,
    conversation_history: list[dict],
    user_id: Optional[uuid.UUID] = None,
) -> Tuple[Optional[str], float]:
    """
    Genera una respuesta AI para un ticket de soporte.

    Quality Gate: if user has quality gate enabled and confidence < threshold,
    returns (None, confidence) to trigger human escalation.

    Returns:
        (response_text, confidence) — confidence 0.0 means "escalate to human"
    """
    # 1. Search FAQ and KB for relevant content
    kb_results = await search_kb_and_faq(db, business_id, ticket_title + " " + ticket_description)

    context = ""
    if kb_results:
        context = "Relevant documentation:\n"
        for result in kb_results[:3]:
            context += f"- {result['title']}: {result['content'][:300]}\n"

    # 2. Build conversation history
    history = ""
    for msg in conversation_history[-5:]:
        sender = msg.get("sender_type", "user")
        content = msg.get("content", "")
        history += f"{sender}: {content}\n"

    system_prompt = """You are a helpful and professional technical support agent.
Your goal is to solve customer issues efficiently and accurately.

Rules:
- Be concise but thorough
- If you don't know the answer or the issue requires human intervention, say "ESCALATE"
- Never make up information not present in the context
- Provide step-by-step instructions when relevant
- Be empathetic and professional
- Respond in the same language as the customer's message"""

    user_prompt = f"""{context}

Ticket: {ticket_title}
Description: {ticket_description}

Conversation:
{history}

Provide a helpful response. If you cannot help, respond with exactly "ESCALATE"."""

    try:
        response = await generate_raw_ai_response(
            db=db,
            business_id=business_id,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=800,
            temperature=0.3,
        )

        if not response:
            return None, 0.0

        if "ESCALATE" in response.upper():
            return None, 0.0

        # Simple confidence heuristic based on context presence
        confidence = 0.85 if kb_results else 0.55
        if len(response) < 50:
            confidence *= 0.8
        confidence = min(confidence, 0.95)

        # Quality Gate check
        if user_id:
            try:
                from app.domains.consumo.service import get_or_create_quality_gate_config
                qg = await get_or_create_quality_gate_config(db, user_id)
                if qg.enabled and confidence < qg.min_confidence_threshold:
                    # Store as draft suggestion but don't send to user
                    return None, confidence
            except Exception:
                pass  # If quality gate fails, proceed normally

        return response.strip(), confidence
    except Exception:
        return None, 0.0


async def should_escalate(
    db: AsyncSession,
    ticket_id: uuid.UUID,
    message_count: int,
    ai_message_count: int,
) -> bool:
    """Determina si un ticket debe escalarse a humano."""
    if ai_message_count >= MAX_AI_MESSAGES_BEFORE_ESCALATE:
        return True

    svc = SupportService(db)
    messages = await svc.list_messages(ticket_id)

    # Check if user sent multiple messages without resolution
    user_msgs = [m for m in messages if m.sender_type.value == "user"]
    ai_msgs = [m for m in messages if m.sender_type.value == "ai"]

    if len(ai_msgs) >= MAX_AI_MESSAGES_BEFORE_ESCALATE and len(user_msgs) > len(ai_msgs):
        return True

    return False
