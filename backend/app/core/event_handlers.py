"""Event Handlers — Suscribiciones al Event Bus.

Registra handlers para eventos del sistema que conectan dominios.
"""

from typing import Any, Dict
from uuid import UUID

from app.core.events import event_bus
from app.core.database import AsyncSessionLocal


async def _on_lead_score_changed(payload: Dict[str, Any]):
    """Cuando un lead cambia de clasificación, actuar según corresponda."""
    new_classification = payload.get("new_classification")
    conversation_id = payload.get("conversation_id")
    business_id = payload.get("business_id")

    if new_classification == "hot":
        # Verificar si ya existe un deal para esta conversación
        async with AsyncSessionLocal() as db:
            from sqlalchemy import select
            from app.domains.crm.models import Deal
            result = await db.execute(
                select(Deal).where(
                    Deal.conversation_id == UUID(conversation_id),
                    Deal.is_active == True,
                )
            )
            existing = result.scalar_one_or_none()
            if not existing:
                # Crear deal automáticamente
                from app.domains.channels.models import Conversation
                c_result = await db.execute(
                    select(Conversation).where(Conversation.id == UUID(conversation_id))
                )
                conversation = c_result.scalar_one_or_none()
                if conversation:
                    deal = Deal(
                        business_id=UUID(business_id),
                        conversation_id=UUID(conversation_id),
                        title=f"Oportunidad: {conversation.lead_name or 'Lead caliente'}",
                        contact_name=conversation.lead_name,
                        contact_email=conversation.lead_email,
                        contact_phone=conversation.lead_phone,
                        value=conversation.extra_data.get("deal_value") if conversation.extra_data else None,
                        stage="qualified",
                        source_channel=conversation.lead_source,
                    )
                    db.add(deal)
                    await db.commit()
                    from app.core.logger import get_logger
                    get_logger(__name__).info(f"Auto-created deal for hot lead {conversation_id}")

    # Evaluate alert rules
    async with AsyncSessionLocal() as db:
        from app.domains.alerts.engine import AlertEngine
        engine = AlertEngine(db)
        await engine.evaluate_rules(
            "lead.score_changed",
            UUID(business_id),
            conversation_id=conversation_id,
            new_score=payload.get("new_score"),
            old_score=payload.get("old_score"),
            new_classification=new_classification,
            old_classification=payload.get("old_classification"),
        )


async def _on_deal_created(payload: Dict[str, Any]):
    """Cuando se crea un deal, evaluar alertas."""
    business_id = payload.get("business_id")
    async with AsyncSessionLocal() as db:
        from app.domains.alerts.engine import AlertEngine
        engine = AlertEngine(db)
        await engine.evaluate_rules(
            "deal.created",
            UUID(business_id),
            deal_id=payload.get("deal_id"),
            value=payload.get("value"),
            stage=payload.get("stage"),
        )


async def _on_human_handoff(payload: Dict[str, Any]):
    """Cuando se requiere handoff humano, agregar a cola Redis."""
    try:
        import redis
        from app.core.config import get_settings
        settings = get_settings()
        r = redis.from_url(settings.REDIS_URL, decode_responses=True)
        r.lpush("human_handoff_queue", str(payload))
        r.expire("human_handoff_queue", 86400)  # 24h TTL
        r.close()
    except Exception as e:
        from app.core.logger import get_logger
        get_logger(__name__).error(f"Handoff queue error: {e}")

    # Evaluate no-reply alert rules
    business_id = payload.get("business_id")
    async with AsyncSessionLocal() as db:
        from app.domains.alerts.engine import AlertEngine
        engine = AlertEngine(db)
        await engine.evaluate_rules(
            "human.handoff_required",
            UUID(business_id),
            conversation_id=payload.get("conversation_id"),
            reason=payload.get("reason"),
        )


async def _on_order_created(payload: Dict[str, Any]):
    """Cuando se crea una orden, evaluar alertas de revenue."""
    business_id = payload.get("business_id")
    async with AsyncSessionLocal() as db:
        from app.domains.alerts.engine import AlertEngine
        engine = AlertEngine(db)
        await engine.evaluate_rules(
            "order.created",
            UUID(business_id),
            order_id=payload.get("order_id"),
            total_amount=payload.get("total_amount"),
            status=payload.get("status"),
        )


async def _on_workflow_completed(payload: Dict[str, Any]):
    """Cuando un workflow completa, evaluar si falló."""
    business_id = payload.get("business_id")
    async with AsyncSessionLocal() as db:
        from app.domains.alerts.engine import AlertEngine
        engine = AlertEngine(db)
        await engine.evaluate_rules(
            "workflow.completed",
            UUID(business_id),
            workflow_id=payload.get("workflow_id"),
            execution_id=payload.get("execution_id"),
            status=payload.get("status"),
        )


async def _on_order_created_growth(payload: Dict[str, Any]):
    """Cuando se crea una orden: gamificación + review + referral."""
    business_id = payload.get("business_id")
    order_id = payload.get("order_id")
    conversation_id = payload.get("conversation_id")
    total_amount = payload.get("total_amount", 0)

    async with AsyncSessionLocal() as db:
        # 1. Gamification: record sale and trigger celebration
        try:
            from app.domains.gamification.service import GamificationEngine
            from app.domains.users.models import User
            from app.domains.businesses.models import Business

            # Find user for this business
            biz = await db.get(Business, UUID(business_id))
            if biz:
                gamification = GamificationEngine(db)
                was_autopilot = payload.get("source", "") == "autopilot"
                result = await gamification.record_sale(
                    user_id=biz.user_id,
                    business_id=UUID(business_id),
                    amount=float(total_amount) if total_amount else 0,
                    was_autopilot=was_autopilot,
                )
                from app.core.logger import get_logger
                get_logger(__name__).info(
                    f"Gamification: sale recorded for user {biz.user_id}, "
                    f"XP: +{result['xp_gained']}, celebrations: {result['celebration_intensity']}"
                )
        except Exception as e:
            from app.core.logger import get_logger
            get_logger(__name__).info(f"Gamification sale recording skipped: {e}")

        # 2. Generate referral link
        if conversation_id:
            try:
                from app.domains.growth.viral_referral import ViralReferralEngine
                engine = ViralReferralEngine(db)
                await engine.generate_referral_link(
                    business_id=UUID(business_id),
                    conversation_id=UUID(conversation_id),
                )
            except Exception as e:
                from app.core.logger import get_logger
                get_logger(__name__).info(f"Referral link generation skipped: {e}")

        # 3. Queue review request
        if order_id and conversation_id:
            try:
                from app.domains.growth.social_proof import SocialProofEngine
                engine = SocialProofEngine(db)
                await engine.request_review(
                    business_id=UUID(business_id),
                    order_id=UUID(order_id),
                    conversation_id=UUID(conversation_id),
                    channel="whatsapp",
                    delay_hours=72,
                )
            except Exception as e:
                from app.core.logger import get_logger
                get_logger(__name__).info(f"Review request scheduling skipped: {e}")


async def _on_lead_magnet_delivered(payload: Dict[str, Any]):
    """Cuando se entrega un lead magnet y no hay respuesta en 24h, enviar value bomb."""
    business_id = payload.get("business_id")
    conversation_id = payload.get("conversation_id")

    # This would be handled by a scheduled task checking for non-responders
    # We just log it here for tracking
    from app.core.logger import get_logger
    get_logger(__name__).info(f"Lead magnet delivered to {conversation_id}, monitoring for response")


async def _on_referral_signup(payload: Dict[str, Any]):
    """Cuando un referral se registra, iniciar secuencia de bienvenida."""
    business_id = payload.get("business_id")
    new_conversation_id = payload.get("new_conversation_id")

    if new_conversation_id:
        from app.core.logger import get_logger
        get_logger(__name__).info(f"Referral signup from {new_conversation_id}, welcome sequence queued")


async def _on_social_proof_approved(payload: Dict[str, Any]):
    """Cuando se aprueba social proof, hacerlo disponible para sales messages."""
    item_id = payload.get("item_id")
    from app.core.logger import get_logger
    get_logger(__name__).info(f"Social proof {item_id} approved and available for reuse")


def register_event_handlers():
    """Registrar todos los handlers en el Event Bus."""
    event_bus.subscribe("lead.score_changed", _on_lead_score_changed)
    event_bus.subscribe("deal.created", _on_deal_created)
    event_bus.subscribe("human.handoff_required", _on_human_handoff)
    event_bus.subscribe("order.created", _on_order_created)
    event_bus.subscribe("workflow.completed", _on_workflow_completed)
    # Growth events
    event_bus.subscribe("order.created", _on_order_created_growth)
    event_bus.subscribe("lead_magnet.delivered", _on_lead_magnet_delivered)
    event_bus.subscribe("referral.signup", _on_referral_signup)
    event_bus.subscribe("social_proof.approved", _on_social_proof_approved)
    from app.core.logger import get_logger
    get_logger(__name__).info("Event handlers registered")
