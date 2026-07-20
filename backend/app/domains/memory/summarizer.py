"""Conversation Summarization

Fetches conversation memory chunks, generates a summary via LLM,
stores it in AgentConversation.context_summary, and extracts key facts
into CustomerMemory records.
"""

import uuid
import json
from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.memory.models import ConversationMemoryChunk, CustomerMemory
from app.domains.channels.models import Conversation
from app.domains.agents.models import AgentConversation
from app.domains.agents.ai_reply import generate_raw_ai_response
from app.core.logger import get_logger

logger = get_logger(__name__)

_SUMMARY_PROMPT = (
    "Resume esta conversación de ventas extrayendo: tema principal, estado del deal, "
    "objeciones, próximos pasos.\n\n"
    "Conversación:\n{conversation_text}\n\n"
    "Resumen:"
)

_FACT_EXTRACTION_PROMPT = (
    "Extrae hechos clave de este cliente: preferencias, objeciones, presupuesto, "
    "canal preferido, horario ideal, historial de compras, pain points. "
    "Devuelve JSON con formato: {\"facts\": [{\"type\": \"...\", \"content\": \"...\", \"confidence\": 0.9}]}\n\n"
    "Conversación:\n{conversation_text}\n\n"
    "JSON:"
)


async def summarize_conversation(
    db: AsyncSession,
    conversation_id: uuid.UUID,
) -> Optional[str]:
    """
    1. Fetch all messages from conversation_memory_chunks for the conversation.
    2. Build prompt and call LLM (cheapest model via existing router).
    3. Store summary in AgentConversation.context_summary if the record exists.
    4. Extract key facts and store in CustomerMemory.
    """
    result = await db.execute(
        select(ConversationMemoryChunk)
        .where(ConversationMemoryChunk.conversation_id == conversation_id)
        .order_by(ConversationMemoryChunk.chunk_index.asc())
    )
    chunks = result.scalars().all()
    if not chunks:
        logger.info(f"No chunks found for conversation {conversation_id}")
        return None

    conversation_text = "\n".join(f"{c.role}: {c.content}" for c in chunks)

    # Resolve business_id from chunks or the Conversation record
    business_id = chunks[0].business_id
    if not business_id:
        conv_result = await db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conv = conv_result.scalar_one_or_none()
        if conv:
            business_id = conv.business_id

    if not business_id:
        logger.warning(f"No business_id found for conversation {conversation_id}")
        return None

    # Build prompt and call LLM
    prompt = _SUMMARY_PROMPT.format(conversation_text=conversation_text)
    summary = await generate_raw_ai_response(
        db=db,
        business_id=business_id,
        system_prompt=(
            "Eres un asistente de ventas experto. Resume conversaciones de forma "
            "concisa y accionable en español."
        ),
        user_prompt=prompt,
        max_tokens=800,
        temperature=0.3,
    )

    if not summary:
        logger.warning(f"LLM returned no summary for conversation {conversation_id}")
        return None

    # Store summary in AgentConversation.context_summary if the record exists
    agent_conv_result = await db.execute(
        select(AgentConversation).where(AgentConversation.id == conversation_id)
    )
    agent_conv = agent_conv_result.scalar_one_or_none()
    if agent_conv:
        agent_conv.context_summary = summary
        await db.commit()
        logger.info(f"Updated context_summary for AgentConversation {conversation_id}")
    else:
        logger.info(
            f"No AgentConversation found with id {conversation_id}, "
            "skipping summary storage"
        )

    # Extract key facts and store in CustomerMemory
    await _extract_and_store_facts(db, conversation_id, chunks, business_id)

    return summary


async def _extract_and_store_facts(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    chunks: List[ConversationMemoryChunk],
    business_id: uuid.UUID,
) -> None:
    """Helper to extract facts from conversation chunks and persist them."""
    conversation_text = "\n".join(f"{c.role}: {c.content}" for c in chunks)
    prompt = _FACT_EXTRACTION_PROMPT.format(conversation_text=conversation_text)

    facts_json = await generate_raw_ai_response(
        db=db,
        business_id=business_id,
        system_prompt=(
            "Eres un extractor de datos de ventas. Extrae hechos clave del cliente "
            "en JSON válido. Usa tipos: preference, objection, budget, channel, "
            "schedule, purchase_history, pain_point."
        ),
        user_prompt=prompt,
        max_tokens=1200,
        temperature=0.2,
    )

    if not facts_json:
        return

    try:
        data = json.loads(facts_json)
        facts = data.get("facts", [])
    except json.JSONDecodeError:
        logger.warning(f"Failed to parse facts JSON for conversation {conversation_id}")
        return

    customer_id = chunks[0].user_id
    if not customer_id:
        logger.info(f"No customer_id in chunks for conversation {conversation_id}")
        return

    from app.domains.memory.service import MemoryEngine

    engine = MemoryEngine(db)
    for fact in facts:
        mem_type = fact.get("type", "preference")
        content = fact.get("content", "").strip()
        confidence = float(fact.get("confidence", 0.7))
        if content:
            await engine.store_customer_fact(
                business_id=business_id,
                customer_id=customer_id,
                memory_type=mem_type,
                content=content,
                confidence=confidence,
                source_conversation_id=conversation_id,
            )
    logger.info(
        f"Stored {len(facts)} facts for customer {customer_id} "
        f"from conversation {conversation_id}"
    )
