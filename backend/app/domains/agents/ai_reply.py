"""AI Reply Generator — Centralized AI response generation for all channels.

Used by workflow engine, chatbot rules, and any other system component
that needs to generate AI responses with expert voice composition.
"""

import uuid
from typing import Dict, Any, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from app.domains.agents.models import AgentPersonality
from app.domains.agents.prompts import compose_system_prompt, get_system_prompt
from app.domains.channels.models import Conversation, Message
from app.domains.businesses.models import Business
from app.core.logger import get_logger


async def generate_ai_response(
    db: AsyncSession,
    conversation: Conversation,
    personality_slug: str,
    business_id: uuid.UUID,
    custom_prompt: str = "",
    voice_slug: Optional[str] = None,
    max_tokens: int = 1500,
) -> Optional[str]:
    """
    Generate an AI response for a conversation using a personality + optional expert voice.

    Args:
        db: Database session
        conversation: The channel conversation
        personality_slug: Base functional personality (e.g., 'captador', 'vendedor')
        business_id: Business UUID
        custom_prompt: Additional instructions for this specific response
        voice_slug: Optional expert voice to layer over the base personality
        max_tokens: Max tokens for the response

    Returns:
        The generated response text, or None if generation failed
    """
    # Validate personality exists
    result = await db.execute(
        select(AgentPersonality).where(AgentPersonality.slug == personality_slug)
    )
    personality = result.scalar_one_or_none()
    if not personality:
        from app.core.logger import get_logger
        get_logger(__name__).warning(f"Personality '{personality_slug}' not found")
        return None

    # Build business context
    business_context = {}
    try:
        from app.domains.agents.context_builder import BusinessContextBuilder
        ctx_builder = BusinessContextBuilder(db)
        business_context = await ctx_builder.build_system_prompt_context(
            business_id=business_id,
            personality_slug=personality_slug,
        )
        # Extract voice from config if not explicitly provided
        if not voice_slug:
            voice_slug = business_context.pop("voice_personality_slug", None)
        else:
            business_context.pop("voice_personality_slug", None)
    except Exception as e:
        from app.core.logger import get_logger
        get_logger(__name__).error(f"Context builder error: {e}")

    # Build system prompt with voice composition
    if voice_slug:
        system_prompt = compose_system_prompt(
            base_slug=personality.slug,
            voice_slug=voice_slug,
            business_context=business_context or {},
        )
    else:
        system_prompt = get_system_prompt(
            personality.slug,
            business_context=business_context or {},
        )

    # Check for active A/B test
    try:
        from app.domains.agents.ab_service import ABTestEngine

        ab_engine = ABTestEngine()
        experiment = await ab_engine.get_active_experiment_for_agent(
            db, personality_slug
        )
        if experiment:
            variant = ab_engine.get_variant_for_conversation(
                db, experiment.id, conversation.id
            )
            if variant == "a":
                system_prompt = experiment.variant_a_prompt
            else:
                system_prompt = experiment.variant_b_prompt
    except Exception as e:
        get_logger(__name__).warning(f"A/B test lookup failed: {e}")

    # Inject CustomerMemory profile into the prompt
    customer_profile = ""
    try:
        from app.domains.memory.service import MemoryEngine
        from app.domains.memory.models import ConversationMemoryChunk

        engine = MemoryEngine(db)
        cust_result = await db.execute(
            select(ConversationMemoryChunk.user_id)
            .where(ConversationMemoryChunk.conversation_id == conversation.id)
            .limit(1)
        )
        customer_id = cust_result.scalar_one_or_none()
        if customer_id:
            customer_profile = await engine.get_customer_profile_summary(customer_id)
    except Exception as e:
        get_logger(__name__).warning(f"Failed to load customer profile: {e}")

    if custom_prompt:
        system_prompt += f"\n\nINSTRUCTION: {custom_prompt}"

    if customer_profile:
        system_prompt += f"\n\n{customer_profile}"

    # Get recent conversation history
    result = await db.execute(
        select(Message).where(
            Message.conversation_id == conversation.id
        ).order_by(Message.created_at.desc()).limit(10)
    )
    recent_msgs = list(reversed(result.scalars().all()))

    # --- Emotional Intelligence ---
    latest_customer_msg = None
    latest_customer_msg_id = None
    for msg in reversed(recent_msgs):
        if msg.direction.value == "inbound":
            latest_customer_msg = msg
            latest_customer_msg_id = msg.id
            break

    if latest_customer_msg:
        try:
            from app.domains.agents.emotion_engine import EmotionDetector, ToneAdapter

            emotion = await EmotionDetector.detect_emotion(
                db=db,
                business_id=business_id,
                message=latest_customer_msg.content,
                conversation_history=[m.content for m in recent_msgs],
                message_id=latest_customer_msg_id,
                conversation_id=conversation.id,
            )
            system_prompt = ToneAdapter.adapt_tone(system_prompt, emotion)
        except Exception as e:
            get_logger(__name__).warning(f"Emotion detection failed: {e}")

    # --- Negotiation Engine ---
    if latest_customer_msg:
        try:
            from app.domains.agents.negotiation_engine import NegotiationEngine

            neg_engine = NegotiationEngine(db)
            is_negotiation = await neg_engine.detect_negotiation_intent(
                latest_customer_msg.content,
                business_id=business_id,
            )
            if is_negotiation:
                state = await neg_engine.get_active_state(conversation.id)
                offer = neg_engine.extract_offer_amount(latest_customer_msg.content)

                if state and offer:
                    neg_resp = await neg_engine.process_offer(conversation.id, offer)
                    reply = await neg_engine.generate_negotiation_reply(
                        business_id=business_id,
                        negotiation_response=neg_resp,
                        state=state,
                    )
                    return reply

                if state:
                    # Active negotiation but no clear offer
                    reply = await generate_raw_ai_response(
                        db=db,
                        business_id=business_id,
                        system_prompt=(
                            f"{system_prompt}\n\n"
                            "Estás negociando precio con este cliente. "
                            "Pide amablemente que aclare su oferta numérica."
                        ),
                        user_prompt=latest_customer_msg.content,
                        max_tokens=max_tokens,
                        temperature=0.7,
                    )
                    return reply

                # No active state - generic negotiation opener
                reply = await generate_raw_ai_response(
                    db=db,
                    business_id=business_id,
                    system_prompt=(
                        f"{system_prompt}\n\n"
                        "El cliente quiere negociar el precio. "
                        "Pregunta amablemente cuál es su presupuesto o qué precio tenía en mente."
                    ),
                    user_prompt=latest_customer_msg.content,
                    max_tokens=max_tokens,
                    temperature=0.7,
                )
                return reply
        except Exception as e:
            get_logger(__name__).warning(f"Negotiation engine failed: {e}")

    # Rebuild messages list after potential system_prompt changes
    messages = [SystemMessage(content=system_prompt)]
    for msg in recent_msgs:
        role = "user" if msg.direction.value == "inbound" else "assistant"
        if role == "user":
            messages.append(HumanMessage(content=msg.content))
        else:
            messages.append(AIMessage(content=msg.content))

    # Generate using fallback provider (OpenAI -> Anthropic)
    try:
        from app.domains.agents.llm_provider import generate_with_fallback
        response = await generate_with_fallback(
            db=db,
            business_id=business_id,
            messages=messages,
            model="gpt-4o-mini",
            temperature=0.7,
            max_tokens=max_tokens,
        )
        result = response.content if response else None
    except Exception as e:
        get_logger(__name__).error(f"LLM invocation failed: {e}")
        result = None

    # After reply, trigger fact extraction every N messages
    if result:
        try:
            msg_count_result = await db.execute(
                select(func.count(Message.id)).where(
                    Message.conversation_id == conversation.id
                )
            )
            msg_count = msg_count_result.scalar() or 0
            if msg_count > 0 and msg_count % 10 == 0:
                from app.domains.memory.service import MemoryEngine

                mem_engine = MemoryEngine(db)
                await mem_engine.extract_facts_from_conversation(conversation.id)
        except Exception as e:
            get_logger(__name__).warning(f"Failed to trigger fact extraction: {e}")

    # --- Chain-of-Thought logging for complex responses ---
    is_complex = bool(
        custom_prompt
        or (len(recent_msgs) > 5)
        or (latest_customer_msg and len(latest_customer_msg.content) > 100)
    )
    if result and is_complex:
        try:
            from app.domains.agents.reflection import ChainOfThought

            query = latest_customer_msg.content if latest_customer_msg else ""
            tools_used = []
            if custom_prompt:
                # Heuristic: extract tool names from custom_prompt
                import re
                tools_used = re.findall(r"\[([^\]]+)\]", custom_prompt)

            thought_steps = await ChainOfThought.generate_thought_process(
                db=db,
                query=query,
                context={
                    "business_id": str(business_id),
                    "personality_slug": personality_slug,
                    "voice_slug": voice_slug,
                    "custom_prompt": custom_prompt,
                    "message_count": len(recent_msgs),
                },
                tools_used=tools_used,
            )
            if thought_steps:
                await ChainOfThought.log_thought_process(
                    db=db,
                    conversation_id=conversation.id,
                    message_id=latest_customer_msg_id,
                    thought_steps=thought_steps,
                )
        except Exception as e:
            get_logger(__name__).warning(f"Chain-of-thought logging failed: {e}")

    return result


async def generate_raw_ai_response(
    db: AsyncSession,
    business_id: uuid.UUID,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 1500,
    temperature: float = 0.7,
) -> Optional[str]:
    """Generate a raw AI response without requiring a conversation.

    Useful for background tasks, notifications, and analytics where
    no conversation context exists.
    """
    try:
        from app.domains.agents.llm_provider import generate_with_fallback
        response = await generate_with_fallback(
            db=db,
            business_id=business_id,
            messages=[
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ],
            model="gpt-4o-mini",
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.content if response else None
    except Exception as e:
        get_logger(__name__).error(f"Raw LLM invocation failed: {e}")
        return None
