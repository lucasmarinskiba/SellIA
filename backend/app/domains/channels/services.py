from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import Any, Optional

from app.domains.channels.models import (
    ChannelConnection, ChannelPlatform, Conversation, Message,
    MessageDirection, MessageStatus, ConversationStatus
)
from app.domains.channels.schemas import WebhookPayload
from app.domains.automations.models import WorkflowTriggerType, ChatbotRule
from app.domains.channels.connectors import get_connector


async def _ai_classify_intent(
    db: AsyncSession,
    business_id: Any,
    content: str,
    available_intents: list[str],
) -> Optional[str]:
    """Use AI to classify the intent of an inbound message.

    Returns the matched intent slug from available_intents, or None.
    """
    if not content or not available_intents:
        return None

    try:
        from app.domains.businesses.models import Business
        from app.domains.agents.llm_provider import generate_with_fallback
        from langchain_core.messages import SystemMessage, HumanMessage

        result = await db.execute(
            select(Business).where(Business.id == business_id)
        )
        business = result.scalar_one_or_none()
        if not business:
            return None

        system_prompt = """You are an Intent Classification AI for a sales chatbot.
Your job is to analyze customer messages and classify them into one of the available intents.

RULES:
- Respond with ONLY the intent name. No explanations, no punctuation.
- If none match perfectly, choose the closest one.
- If the message is completely unrelated, respond with "default".
- Consider context, synonyms, and implied meaning. Don't just look for keywords.

Examples:
- "How much does it cost?" → price
- "I want to book a call" → appointment
- "This is a scam" → complaint
- "Thanks, bye" → goodbye
- "Just looking around" → default"""

        user_prompt = f"""Available intents: {', '.join(available_intents)}

Customer message: "{content[:500]}"

Intent:"""

        messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
        response = await generate_with_fallback(
            db, business_id, messages, model="llama3.1", temperature=0.1, max_tokens=50,
        )
        if not response:
            return None
        detected_intent = response.content.strip().lower()

        # Validate against available intents
        for intent in available_intents:
            if detected_intent == intent.lower():
                return intent

        return None
    except Exception as e:
        from app.core.logger import get_logger
        get_logger(__name__).error(f"AI intent classification error: {e}")
        return None


async def _detect_competitor_mentions(
    db: AsyncSession,
    conversation: Conversation,
    content: str,
    business_id: Any,
):
    """Detect competitor mentions in incoming messages using AI.

    Stores detected competitors in conversation.extra_data['competitor_mentions'].
    Triggers a workflow event if competitors are found.
    """
    if not content:
        return

    try:
        from app.domains.agents.ai_reply import generate_raw_ai_response

        system_prompt = """You are a competitor detection AI for a sales system.
Your job is to analyze customer messages and detect if they mention any competitor brands, products, or services.

RULES:
- Respond with ONLY a JSON array of competitor names. Example: ["CompetidorX", "CompetidorY"]
- If no competitors are mentioned, respond with: []
- Be precise. Don't hallucinate competitors.
- Consider indirect mentions and comparisons."""

        user_prompt = f"""Analyze this customer message and extract any competitor mentions:

"{content[:800]}"

Competitors (JSON array only):"""

        ai_response = await generate_raw_ai_response(
            db=db,
            business_id=business_id,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=100,
            temperature=0.1,
        )

        if not ai_response:
            return

        import json
        try:
            competitors = json.loads(ai_response.strip())
        except json.JSONDecodeError:
            # Fallback: try to extract from plain text
            competitors = []
            for line in ai_response.split("\n"):
                line = line.strip().strip("[]\"'",)
                if line and line not in ("[", "]", "", "null", "None"):
                    competitors.append(line)

        if not competitors:
            return

        # Store in conversation extra_data
        if not conversation.extra_data:
            conversation.extra_data = {}
        existing = conversation.extra_data.get("competitor_mentions", [])
        for comp in competitors:
            if comp not in existing:
                existing.append(comp)
        conversation.extra_data["competitor_mentions"] = existing
        await db.commit()

        # Emit event
        try:
            from app.core.events import event_bus
            await event_bus.emit(
                "competitor.mentioned",
                {
                    "business_id": str(business_id),
                    "conversation_id": str(conversation.id),
                    "competitors": competitors,
                    "message_snippet": content[:200],
                },
            )
        except Exception:
            pass

        # Create Alert + Recommendation
        try:
            from app.domains.alerts.models import Alert, AlertSeverity, AlertStatus, Recommendation, RecommendationType, RecommendationActionType, RecommendationStatus
            alert = Alert(
                business_id=business_id,
                conversation_id=conversation.id,
                title=f"Mención de competidor: {', '.join(competitors[:3])}",
                description=f"El lead mencionó a: {', '.join(competitors)}. Mensaje: {content[:200]}",
                severity=AlertSeverity.WARNING,
                status=AlertStatus.UNREAD,
                entity_type="conversation",
                entity_id=conversation.id,
                recommended_action="Responder con diferenciador competitivo",
                alert_metadata={"competitors": competitors, "message_snippet": content[:200]},
            )
            db.add(alert)
            await db.flush()

            recommendation = Recommendation(
                business_id=business_id,
                conversation_id=conversation.id,
                type=RecommendationType.CUSTOM,
                title=f"Responde al lead sobre {competitors[0]}",
                description=f"El lead mencionó a {', '.join(competitors)}. Es una oportunidad para destacar tu diferenciación.",
                priority=3,
                context_data={"competitors": competitors, "message_snippet": content[:200]},
                action_type=RecommendationActionType.SEND_MESSAGE,
                action_payload={"conversation_id": str(conversation.id), "suggested_content": "Enviar diferenciador competitivo"},
                status=RecommendationStatus.PENDING,
            )
            db.add(recommendation)
            await db.commit()
        except Exception as e:
            from app.core.logger import get_logger
            get_logger(__name__).error(f"Competitor alert creation error: {e}")

    except Exception as e:
        from app.core.logger import get_logger
        get_logger(__name__).error(f"Competitor detection inner error: {e}")


async def _evaluate_chatbot_rules(
    db: AsyncSession,
    business_id: Any,
    platform: ChannelPlatform,
    content: str,
) -> Optional[ChatbotRule]:
    """Evaluar reglas de chatbot y devolver la primera que haga match.

    First tries keyword matching. If no match, falls back to AI intent classification.
    """
    result = await db.execute(
        select(ChatbotRule).where(
            ChatbotRule.business_id == business_id,
            ChatbotRule.is_active == True,
        ).order_by(desc(ChatbotRule.priority))
    )
    rules = result.scalars().all()

    content_lower = (content or "").lower()

    # Phase 1: Keyword matching (fast)
    for rule in rules:
        if rule.channel_filter and platform.value not in rule.channel_filter:
            continue
        if rule.keywords:
            if any(kw.lower() in content_lower for kw in rule.keywords):
                return rule

    # Phase 2: AI intent classification (when no keyword match)
    available_intents = [r.intent for r in rules if r.intent]
    if available_intents:
        detected_intent = await _ai_classify_intent(db, business_id, content, available_intents)
        if detected_intent:
            for rule in rules:
                if rule.channel_filter and platform.value not in rule.channel_filter:
                    continue
                if rule.intent.lower() == detected_intent.lower():
                    return rule

    return None


async def _apply_chatbot_rule(
    db: AsyncSession,
    rule: ChatbotRule,
    conversation: Conversation,
    platform: ChannelPlatform,
) -> bool:
    """Aplicar una regla de chatbot. Devuelve True si se respondió automáticamente."""
    # Incrementar usage count
    rule.usage_count += 1
    await db.commit()

    if rule.requires_human:
        # Marcar conversación y emitir evento de handoff
        conversation.status = ConversationStatus.ACTIVE
        if not conversation.extra_data:
            conversation.extra_data = {}
        conversation.extra_data["awaiting_human"] = True
        conversation.extra_data["handoff_reason"] = f"Regla chatbot: {rule.name} ({rule.intent})"
        await db.commit()

        try:
            from app.core.events import emit_human_handoff_required
            await emit_human_handoff_required(
                business_id=str(conversation.business_id),
                conversation_id=str(conversation.id),
                platform=platform.value,
                reason=f"Regla '{rule.name}' requiere humano: {rule.intent}",
                lead_name=conversation.lead_name,
            )
        except Exception as e:
            from app.core.logger import get_logger
            get_logger(__name__).error(f"Handoff emit error: {e}")
        return True

    # Responder según tipo
    if rule.response_type == "text":
        response_text = rule.response_template
    elif rule.response_type == "template":
        # TODO: resolver template con variables de conversación
        response_text = rule.response_template
    elif rule.response_type == "ai_generated":
        # Generate AI response using personality + optional expert voice
        from app.domains.agents.ai_reply import generate_ai_response
        personality_slug = rule.extra_data.get("personality_slug", "captador") if rule.extra_data else "captador"
        ai_response = await generate_ai_response(
            db=db,
            conversation=conversation,
            personality_slug=personality_slug,
            business_id=conversation.business_id,
            custom_prompt=rule.response_template,
        )
        response_text = ai_response or rule.response_template
    else:
        response_text = rule.response_template

    if response_text:
        try:
            await send_outbound_message(db, conversation.id, response_text)
        except Exception as e:
            from app.core.logger import get_logger
            get_logger(__name__).error(f"Chatbot rule send error: {e}")

    return True


async def _maybe_ai_auto_reply(
    db: AsyncSession,
    channel: ChannelConnection,
    conversation: Conversation,
    payload: WebhookPayload,
):
    """Send an AI-generated auto-reply if no response was sent and the business has it enabled."""
    # Skip if the conversation is awaiting human
    if conversation.extra_data and conversation.extra_data.get("awaiting_human"):
        return

    # Skip non-chat platforms (ads, e-commerce notifications)
    if payload.content_type in ("order", "abandoned_cart", "customer", "system", "lead"):
        return

    # Check if any outbound message was sent in the last 30 seconds
    from sqlalchemy import func
    recent_outbound = await db.execute(
        select(Message).where(
            Message.conversation_id == conversation.id,
            Message.direction == MessageDirection.OUTBOUND,
            Message.created_at >= func.now() - func.interval("30 seconds"),
        )
    )
    if recent_outbound.scalar_one_or_none():
        return

    # Check business AI auto-reply config
    from app.domains.agents.models import AgentConfig
    result = await db.execute(
        select(AgentConfig).where(
            AgentConfig.business_id == channel.business_id,
            AgentConfig.is_enabled == True,
            AgentConfig.ai_auto_reply_enabled == True,
        )
    )
    agent_config = result.scalar_one_or_none()
    if not agent_config:
        return

    # Determine personality to use
    personality_slug = "captador"
    voice_slug = None
    if agent_config.ai_auto_reply_personality_id:
        from app.domains.agents.models import AgentPersonality
        personality_result = await db.execute(
            select(AgentPersonality).where(AgentPersonality.id == agent_config.ai_auto_reply_personality_id)
        )
        personality = personality_result.scalar_one_or_none()
        if personality:
            personality_slug = personality.slug
    elif agent_config.personality_id:
        personality_result = await db.execute(
            select(AgentPersonality).where(AgentPersonality.id == agent_config.personality_id)
        )
        personality = personality_result.scalar_one_or_none()
        if personality:
            personality_slug = personality.slug

    # Generate AI response
    from app.domains.agents.ai_reply import generate_ai_response
    ai_response = await generate_ai_response(
        db=db,
        conversation=conversation,
        personality_slug=personality_slug,
        business_id=channel.business_id,
        voice_slug=voice_slug,
    )
    if ai_response:
        await send_outbound_message(db, conversation.id, ai_response)


async def process_incoming_message(
    db: AsyncSession,
    channel: ChannelConnection,
    payload: WebhookPayload,
):
    """Procesa un mensaje entrante para un canal específico.
    
    El canal ya debe estar identificado y autenticado por el caller.
    """
    if not channel or not channel.is_active:
        return

    # Buscar o crear conversación
    result = await db.execute(
        select(Conversation).where(
            Conversation.business_id == channel.business_id,
            Conversation.external_id == payload.external_id,
            Conversation.is_active == True,
        )
    )
    conversation = result.scalar_one_or_none()
    is_new_conversation = conversation is None

    if not conversation:
        conversation = Conversation(
            business_id=channel.business_id,
            channel_connection_id=channel.id,
            external_id=payload.external_id,
            lead_name=payload.sender_name,
            lead_email=payload.sender_email,
            lead_phone=payload.sender_phone,
            lead_source=channel.platform.value,
            status=ConversationStatus.ACTIVE,
        )
        db.add(conversation)
        await db.flush()

    # Crear mensaje
    message = Message(
        conversation_id=conversation.id,
        direction=MessageDirection.INBOUND,
        content=payload.content,
        content_type=payload.content_type,
        status=MessageStatus.DELIVERED,
        extra_data=payload.extra_data or {},
    )
    db.add(message)
    await db.flush()

    conversation.last_message_at = message.created_at
    await db.commit()

    # === Procesar confirmaciones de citas ===
    try:
        await _process_appointment_confirmation(db, conversation, payload.content)
    except Exception as e:
        from app.core.logger import get_logger
        get_logger(__name__).error(f"Appointment confirmation error: {e}")

    # === Emitir evento de mensaje recibido ===
    try:
        from app.core.events import emit_message_received
        await emit_message_received(
            business_id=str(channel.business_id),
            conversation_id=str(conversation.id),
            platform=channel.platform.value,
            content=payload.content,
            sender_name=payload.sender_name,
            is_new_conversation=is_new_conversation,
        )
    except Exception as e:
        from app.core.logger import get_logger
        get_logger(__name__).error(f"Event emit error: {e}")

    # === Evaluar Chatbot Rules primero ===
    matched_rule = await _evaluate_chatbot_rules(
        db, channel.business_id, channel.platform, payload.content
    )
    if matched_rule:
        await _apply_chatbot_rule(db, matched_rule, conversation, channel.platform)
        # Si la regla responde automáticamente y NO requiere humano,
        # igual permitimos que workflows se disparen para tagging/scoring
        # pero NO para AI reply (la regla ya respondió)
        if not matched_rule.requires_human:
            # Solo triggers de scoring/tagging, no AI reply
            pass

    # === Recalcular Lead Score ===
    try:
        from app.domains.crm.scoring import LeadScoringEngine
        scoring_engine = LeadScoringEngine(db)
        await scoring_engine.record_activity(
            business_id=channel.business_id,
            conversation_id=conversation.id,
            activity_type="message_received",
            points=5,
            description=f"Mensaje recibido por {channel.platform.value}",
        )
    except Exception as e:
        from app.core.logger import get_logger
        get_logger(__name__).error(f"Lead scoring error: {e}")

    # === Competitor Mention Detection ===
    try:
        await _detect_competitor_mentions(db, conversation, payload.content, channel.business_id)
    except Exception as e:
        from app.core.logger import get_logger
        get_logger(__name__).error(f"Competitor detection error: {e}")

    # === Trigger: NEW_LEAD ===
    if is_new_conversation:
        try:
            from app.domains.automations.engine import WorkflowEngine
            engine = WorkflowEngine(db)
            await engine.process_trigger(
                trigger_type=WorkflowTriggerType.NEW_LEAD,
                business_id=channel.business_id,
                conversation_id=conversation.id,
                trigger_data={
                    "content": payload.content,
                    "channel": channel.platform.value,
                    "sender_name": payload.sender_name,
                    "sender_email": payload.sender_email,
                    "sender_phone": payload.sender_phone,
                },
            )
        except Exception as e:
            from app.core.logger import get_logger
            get_logger(__name__).error(f"NEW_LEAD trigger error: {e}")

    # === E-Commerce Order Bridge ===
    if payload.content_type in ("order", "abandoned_cart"):
        try:
            from app.domains.orders.services import EcommerceWebhookProcessor
            processor = EcommerceWebhookProcessor(db)
            await processor.process_order_webhook(channel, conversation, payload)
        except Exception as e:
            from app.core.logger import get_logger
            get_logger(__name__).error(f"Ecommerce webhook processing error: {e}")

    # === Trigger: ORDER_CREATED / CART_ABANDONED ===
    if payload.content_type == "order":
        try:
            from app.domains.automations.engine import WorkflowEngine
            engine = WorkflowEngine(db)
            await engine.process_trigger(
                trigger_type=WorkflowTriggerType.ORDER_CREATED,
                business_id=channel.business_id,
                conversation_id=conversation.id,
                trigger_data={
                    "content": payload.content,
                    "channel": channel.platform.value,
                    "extra_data": payload.extra_data or {},
                },
            )
            from app.core.events import emit_order_created
            await emit_order_created(
                business_id=str(channel.business_id),
                order_id=str(conversation.external_id),
                total_amount=float(payload.extra_data.get("total_price", 0)) if payload.extra_data else 0,
                status="pending",
                conversation_id=str(conversation.id),
            )
        except Exception as e:
            from app.core.logger import get_logger
            get_logger(__name__).error(f"ORDER_CREATED trigger error: {e}")

    elif payload.content_type == "abandoned_cart":
        try:
            from app.domains.automations.engine import WorkflowEngine
            engine = WorkflowEngine(db)
            await engine.process_trigger(
                trigger_type=WorkflowTriggerType.CART_ABANDONED,
                business_id=channel.business_id,
                conversation_id=conversation.id,
                trigger_data={
                    "content": payload.content,
                    "channel": channel.platform.value,
                    "extra_data": payload.extra_data or {},
                },
            )
        except Exception as e:
            from app.core.logger import get_logger
            get_logger(__name__).error(f"CART_ABANDONED trigger error: {e}")

    # === Trigger: NEW_MESSAGE ===
    try:
        from app.domains.automations.engine import WorkflowEngine
        engine = WorkflowEngine(db)
        await engine.process_trigger(
            trigger_type=WorkflowTriggerType.NEW_MESSAGE,
            business_id=channel.business_id,
            conversation_id=conversation.id,
            trigger_data={
                "content": payload.content,
                "channel": channel.platform.value,
                "sender_name": payload.sender_name,
                "is_new_conversation": is_new_conversation,
                "chatbot_rule_matched": matched_rule.name if matched_rule else None,
                "requires_human": matched_rule.requires_human if matched_rule else False,
            },
        )
    except Exception as e:
        from app.core.logger import get_logger
        get_logger(__name__).error(f"Workflow trigger error: {e}")

    # === AI Default Auto-Reply (safety net) ===
    try:
        await _maybe_ai_auto_reply(db, channel, conversation, payload)
    except Exception as e:
        from app.core.logger import get_logger
        get_logger(__name__).error(f"AI auto-reply error: {e}")


async def send_outbound_message(
    db: AsyncSession,
    conversation_id: Any,
    content: str,
    content_type: str = "text",
) -> dict[str, Any]:
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if not conversation or not conversation.channel_connection_id:
        raise ValueError("Conversación sin canal asociado")

    result = await db.execute(
        select(ChannelConnection).where(
            ChannelConnection.id == conversation.channel_connection_id
        )
    )
    channel = result.scalar_one_or_none()
    if not channel:
        raise ValueError("Canal no encontrado")

    connector = get_connector(channel.platform, channel.credentials, channel.settings)

    recipient = conversation.external_id
    if channel.platform == ChannelPlatform.EMAIL:
        recipient = conversation.lead_email or conversation.external_id

    response = await connector.send_message(recipient, content, content_type)

    message = Message(
        conversation_id=conversation.id,
        direction=MessageDirection.OUTBOUND,
        content=content,
        content_type=content_type,
        status=MessageStatus.SENT,
        extra_data={"api_response": response},
    )
    db.add(message)
    conversation.last_message_at = message.created_at
    await db.commit()

    # === Emitir evento de mensaje enviado ===
    try:
        from app.core.events import emit_message_sent
        await emit_message_sent(
            business_id=str(channel.business_id),
            conversation_id=str(conversation.id),
            platform=channel.platform.value,
            content=content,
        )
    except Exception as e:
        from app.core.logger import get_logger
        get_logger(__name__).error(f"Send event error: {e}")

    return response



async def _process_appointment_confirmation(db, conversation, content: str):
    """Check if incoming message is an appointment confirmation/cancellation response."""
    from sqlalchemy import select
    from app.domains.services.models import Appointment, AppointmentStatus
    from app.domains.services.services import confirm_appointment, cancel_appointment

    # Find pending appointments for this conversation
    result = await db.execute(
        select(Appointment).where(
            Appointment.conversation_id == conversation.id,
            Appointment.status.in_([AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED]),
            Appointment.is_active == True,
        ).order_by(Appointment.start_time)
    )
    appointments = result.scalars().all()
    if not appointments:
        return

    content_lower = content.lower().strip()
    confirmation_keywords = ['si', 'sí', 'confirmar', 'confirmo', 'ok', 'yes', 'dale', 'perfecto', 'genial', 'bien']
    cancellation_keywords = ['no', 'cancelar', 'cancelo', 'no puedo', 'no voy', 'anular', 'no asistiré']

    for appt in appointments:
        if any(kw in content_lower for kw in confirmation_keywords):
            await confirm_appointment(db, appt)
            # Send confirmation back
            await send_outbound_message(
                db,
                conversation.id,
                f"¡Perfecto! Tu cita para *{appt.service_name or 'nuestro servicio'}* el {appt.start_time.strftime('%d/%m/%Y a las %H:%M')} ha sido confirmada. ¡Te esperamos! 🙌",
                content_type="text",
            )
            return
        elif any(kw in content_lower for kw in cancellation_keywords):
            await cancel_appointment(db, appt)
            await send_outbound_message(
                db,
                conversation.id,
                f"Entendido. Tu cita para *{appt.service_name or 'nuestro servicio'}* ha sido cancelada. Si quieres reagendar, escríbenos cuando puedas. 📅",
                content_type="text",
            )
            return
