"""Customer Service Auto-Agent Service"""

import uuid
import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from app.core.logger import get_logger
from app.domains.agents.customer_service.models import ServiceBotConfig, ServiceInteraction
from app.domains.agents.emotion_engine import EmotionDetector
from app.domains.documents.service import DocumentService
from app.domains.memory.service import MemoryEngine
from app.domains.channels.models import Conversation, Message
from app.domains.agents.ai_reply import generate_raw_ai_response

logger = get_logger(__name__)


async def handle_customer_message(
    db: AsyncSession,
    bot_config_id: uuid.UUID,
    customer_id: Optional[uuid.UUID],
    message: str,
    channel: str,
    conversation_id: Optional[uuid.UUID] = None,
) -> Dict[str, Any]:
    """
    1. Detect emotion
    2. Search FAQ/docs via RAG
    3. Search conversation memory for context
    4. Generate response using ReAct + knowledge base
    5. Escalate if needed
    6. Log interaction
    """
    # Load bot config
    result = await db.execute(
        select(ServiceBotConfig).where(ServiceBotConfig.id == bot_config_id)
    )
    config = result.scalar_one_or_none()
    if not config:
        raise ValueError("Bot config not found")

    business_id = config.business_id

    # 1. Detect emotion
    emotion_result = await EmotionDetector.detect_emotion(
        db=db,
        business_id=business_id,
        message=message,
        conversation_history=None,  # Could load recent messages if needed
        conversation_id=conversation_id,
    )

    # 2. Search FAQ/docs
    doc_service = DocumentService(db)
    doc_results = await doc_service.search_documents(business_id, message, k=3)
    faq_context = "\n".join(
        f"- {r['content'][:500]}" for r in doc_results
    )
    query_confidence = 0.5
    if doc_results:
        # Simple confidence heuristic based on top score
        top_score = doc_results[0].get("score", 0.0)
        query_confidence = min(1.0, max(0.0, float(top_score) + 0.5))

    # 3. Conversation memory context
    memory_engine = MemoryEngine(db)
    memory_chunks = await memory_engine.retrieve_relevant(
        query=message,
        conversation_id=conversation_id,
        business_id=business_id,
        customer_id=customer_id,
        k=5,
    )
    memory_context = "\n".join(
        f"- {chunk.content[:300]}" for chunk in memory_chunks
    )

    # 4. Generate response
    system_prompt = (
        f"{config.greeting_message}\n\n"
        "Eres un asistente de atención al cliente. Usa el siguiente contexto para responder:\n"
        f"Contexto de documentos/FAQ:\n{faq_context}\n\n"
        f"Contexto de memoria de conversación:\n{memory_context}\n\n"
        "Reglas:\n"
        "- Responde en español.\n"
        "- Sé claro, conciso y útil.\n"
        "- Si no sabes la respuesta, indica que escalarás con un humano.\n"
        f"- Emoción detectada del cliente: {emotion_result.emotion} (intensidad {emotion_result.intensity:.0%})\n"
    )

    response_text = await generate_raw_ai_response(
        db=db,
        business_id=business_id,
        system_prompt=system_prompt,
        user_prompt=message,
        max_tokens=800,
        temperature=0.6,
    )
    if not response_text:
        response_text = config.fallback_message

    # 5. Escalation check
    escalated, escalation_reason = should_escalate(
        emotion_result.model_dump(),
        query_confidence,
        config.escalation_threshold,
    )

    if escalated:
        response_text = (
            f"{response_text}\n\n"
            f"{config.fallback_message}"
        )

    # 6. Log interaction
    interaction = ServiceInteraction(
        bot_config_id=bot_config_id,
        conversation_id=conversation_id,
        channel=channel,
        customer_id=customer_id,
        messages=[
            {"role": "user", "content": message, "created_at": datetime.now(timezone.utc).isoformat()},
            {"role": "bot", "content": response_text, "created_at": datetime.now(timezone.utc).isoformat()},
        ],
        resolved=not escalated,
        escalated=escalated,
        escalation_reason=escalation_reason if escalated else None,
    )
    db.add(interaction)
    await db.commit()

    return {
        "response": response_text,
        "escalated": escalated,
        "escalation_reason": escalation_reason if escalated else None,
        "emotion": emotion_result.model_dump(),
        "sources": [r.get("title", "Documento") for r in doc_results],
    }


async def get_faq_answer(
    db: AsyncSession,
    business_id: uuid.UUID,
    query: str,
) -> Dict[str, Any]:
    """Semantic search over business documents for FAQ answers."""
    doc_service = DocumentService(db)
    results = await doc_service.search_documents(business_id, query, k=5)

    answer = None
    if results:
        # Use top result as answer summary
        top = results[0]
        answer = top.get("content", "")[:1000]

    return {
        "query": query,
        "answer": answer,
        "sources": results,
    }


def should_escalate(
    emotion_result: Dict[str, Any],
    query_confidence: float,
    escalation_threshold: float,
) -> tuple[bool, Optional[str]]:
    """Decides if human agent is needed."""
    intensity = float(emotion_result.get("intensity", 0.0))
    emotion = emotion_result.get("emotion", "neutral")

    if intensity >= float(escalation_threshold):
        return True, f"Emoción intensa detectada: {emotion} ({intensity:.0%})"

    if query_confidence < 0.3:
        return True, "Confianza de respuesta insuficiente"

    if emotion in ("angry", "frustrated") and intensity > 0.5:
        return True, f"Cliente {emotion} con alta intensidad"

    return False, None


async def list_interactions(
    db: AsyncSession,
    bot_config_id: Optional[uuid.UUID] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[ServiceInteraction]:
    stmt = select(ServiceInteraction).order_by(desc(ServiceInteraction.created_at))
    if bot_config_id:
        stmt = stmt.where(ServiceInteraction.bot_config_id == bot_config_id)
    stmt = stmt.limit(limit).offset(offset)
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_interaction(db: AsyncSession, interaction_id: uuid.UUID) -> Optional[ServiceInteraction]:
    result = await db.execute(
        select(ServiceInteraction).where(ServiceInteraction.id == interaction_id)
    )
    return result.scalar_one_or_none()


async def create_or_update_config(
    db: AsyncSession,
    business_id: uuid.UUID,
    data: Dict[str, Any],
    config_id: Optional[uuid.UUID] = None,
) -> ServiceBotConfig:
    if config_id:
        result = await db.execute(
            select(ServiceBotConfig).where(
                ServiceBotConfig.id == config_id,
                ServiceBotConfig.business_id == business_id,
            )
        )
        config = result.scalar_one_or_none()
        if not config:
            raise ValueError("Config not found")
        for key, value in data.items():
            if hasattr(config, key) and value is not None:
                setattr(config, key, value)
    else:
        data.pop("business_id", None)
        config = ServiceBotConfig(business_id=business_id, **data)
        db.add(config)

    await db.commit()
    await db.refresh(config)
    return config


async def get_config_by_business(db: AsyncSession, business_id: uuid.UUID) -> Optional[ServiceBotConfig]:
    result = await db.execute(
        select(ServiceBotConfig).where(
            ServiceBotConfig.business_id == business_id,
            ServiceBotConfig.is_active == True,
        )
    )
    return result.scalar_one_or_none()
