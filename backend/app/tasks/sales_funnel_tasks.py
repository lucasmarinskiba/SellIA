"""Celery Tasks — Background automation for sales funnel.

Ejecuta fases en background con retry automático + scheduling.

NOTE: every task body below is async internally (they call async services),
but Celery's default worker calls tasks synchronously. Each task wraps its
logic in an inner `async def _run(): ...` invoked via `asyncio.run(...)` —
this file previously used bare `await` inside plain `def` task functions,
which is a SyntaxError and silently prevented the entire module (and every
task in it) from being registered at all.
"""

import asyncio
import logging
from celery import shared_task
from typing import List, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# NOTE: app.domains.computer_use.services imports are deliberately deferred
# to inside each task function (rather than at module level) because that
# package pulls in optional integrations (e.g. Google Calendar) that aren't
# always installed. A missing transitive dependency there must not prevent
# this whole module — including send_follow_ups, which needs none of those
# services — from being importable and registered with Celery.


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def import_and_enrich_leads(self, leads_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Fase 11: Importa + enriquece leads.

    Retries: 3 intentos con delay de 5 minutos.
    """
    async def _run():
        from app.domains.computer_use.services.lead_generator import get_lead_generator

        lead_gen = get_lead_generator()

        imported = await lead_gen.import_leads(leads_data)

        for lead in imported:
            lead = await lead_gen.enrich_lead(lead)
            lead = await lead_gen.score_lead(lead)

        return {
            "status": "success",
            "imported": len(imported),
            "hot": len([l for l in imported if l.quality.value == "hot"]),
            "warm": len([l for l in imported if l.quality.value == "warm"]),
            "cold": len([l for l in imported if l.quality.value == "cold"]),
        }

    try:
        return asyncio.run(_run())
    except Exception as exc:
        logger.error(f"Error importing leads: {exc}")
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def send_outreach_batch(
    self,
    leads: List[Dict[str, Any]],
    channel: str = "email",
) -> Dict[str, Any]:
    """
    Fase 11: Envía outreach a batch de leads.

    Retries: 3 intentos.
    """
    async def _run():
        from app.domains.computer_use.services.lead_generator import get_lead_generator
        from app.domains.computer_use.services.outreach_orchestrator import get_outreach_orchestrator, OutreachChannel

        lead_gen = get_lead_generator()
        outreach = get_outreach_orchestrator()

        imported = await lead_gen.import_leads(leads)

        for lead in imported:
            lead = await lead_gen.enrich_lead(lead)
            lead = await lead_gen.score_lead(lead)

        campaign = await outreach.create_campaign(
            name=f"Outreach {datetime.utcnow().strftime('%Y%m%d%H%M')}",
            target_quality="hot",
            channel=OutreachChannel(channel),
        )

        contacted = 0
        for lead in imported:
            if lead.quality.value == "hot":
                success, msg_id = await outreach.send_outreach(
                    campaign=campaign,
                    lead=lead,
                    sender_name="SellIA Bot",
                    sender_email="bot@sellía.ai",
                )
                if success:
                    contacted += 1

        logger.info(f"Outreach sent to {contacted} leads")

        return {
            "status": "success",
            "campaign_id": campaign.campaign_id,
            "contacted": contacted,
        }

    try:
        return asyncio.run(_run())
    except Exception as exc:
        logger.error(f"Error in outreach: {exc}")
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


@shared_task(bind=True, max_retries=2, default_retry_delay=600)
def send_follow_ups(self) -> Dict[str, Any]:
    """
    Envía follow-ups automáticos, senior-salesperson style: proactive but
    not spammy. Corre diariamente.

    A conversation qualifies for a follow-up when:
    - It's active, not archived/spam, not currently awaiting a human agent
    - It's had at least one real (inbound) message — no cold empty threads
    - Its last message (in either direction) is 24h+ old
    - It hasn't already converted (handled separately by funnel_ab_bridge
      when an order is paid — a converted conversation moves to RETENTION,
      which this task also respects instead of nagging a happy customer)
    - It has fewer than 3 prior automated follow-ups (tracked in
      conversation.extra_data.follow_up_count, mirroring the "Max 3
      intentos" cap already documented here before this rewrite)

    The follow-up message itself is generated via generate_ai_response
    using a custom_prompt that asks the model to write a natural,
    non-repetitive nudge appropriate to the conversation's current funnel
    stage — not a canned "just checking in" template.
    """
    async def _run():
        from sqlalchemy import select, func
        from app.core.database import AsyncSessionLocal
        from app.domains.channels.models import Conversation, Message, ConversationStatus, MessageDirection
        from app.domains.channels.services import send_outbound_message
        from app.domains.agents.models import AgentConfig
        from app.domains.agents.ai_reply import generate_ai_response
        from app.domains.agents.funnel_stage_detector import detect_funnel_stage
        from app.core.prompts.funnel_specialists import FunnelStage

        sent = 0
        skipped = 0
        cutoff = datetime.now().astimezone() - timedelta(hours=24)

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Conversation).where(
                    Conversation.status == ConversationStatus.ACTIVE,
                    Conversation.is_active == True,
                    Conversation.last_message_at != None,
                    Conversation.last_message_at < cutoff,
                )
            )
            candidates = result.scalars().all()

            for conversation in candidates:
                extra = conversation.extra_data or {}
                if extra.get("awaiting_human"):
                    skipped += 1
                    continue

                follow_up_count = extra.get("follow_up_count", 0)
                if follow_up_count >= 3:
                    skipped += 1
                    continue

                inbound_result = await db.execute(
                    select(func.count(Message.id)).where(
                        Message.conversation_id == conversation.id,
                        Message.direction == MessageDirection.INBOUND,
                    )
                )
                if (inbound_result.scalar() or 0) == 0:
                    skipped += 1
                    continue

                # Don't nag an already-converted/retention-stage customer —
                # that's a different job (RETENTION/EXPANSION messaging).
                stage = await detect_funnel_stage(db, conversation.business_id, conversation)
                if stage in (FunnelStage.RETENTION, FunnelStage.EXPANSION):
                    skipped += 1
                    continue

                config_result = await db.execute(
                    select(AgentConfig).where(
                        AgentConfig.business_id == conversation.business_id,
                        AgentConfig.is_enabled == True,
                        AgentConfig.ai_auto_reply_enabled == True,
                    )
                )
                agent_config = config_result.scalar_one_or_none()
                if not agent_config:
                    skipped += 1
                    continue

                try:
                    reply = await generate_ai_response(
                        db=db,
                        conversation=conversation,
                        personality_slug="captador",
                        business_id=conversation.business_id,
                        custom_prompt=(
                            "El cliente no respondió en más de 24 horas. Escribí un mensaje de "
                            "seguimiento breve, natural y no repetitivo — no uses frases genéricas "
                            "tipo 'solo quería hacer un seguimiento'. Retomá el hilo específico de "
                            "la conversación anterior y dale una razón concreta para responder ahora."
                        ),
                    )
                    if reply:
                        await send_outbound_message(db, conversation.id, reply)
                        extra["follow_up_count"] = follow_up_count + 1
                        conversation.extra_data = extra
                        db.add(conversation)
                        await db.commit()
                        sent += 1
                    else:
                        skipped += 1
                except Exception as e:
                    logger.warning(f"Follow-up failed for conversation {conversation.id}: {e}")
                    skipped += 1

        logger.info(f"Follow-ups: sent={sent} skipped={skipped}")
        return {"status": "success", "followups_sent": sent, "skipped": skipped}

    try:
        return asyncio.run(_run())
    except Exception as exc:
        logger.error(f"Error in follow-ups: {exc}")
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


@shared_task(bind=True, max_retries=2, default_retry_delay=300)
def send_welcome_sequences(
    self,
    customers: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Fase 12: Envía email sequences de bienvenida post-compra.

    Corre inmediatamente después de nueva compra.
    """
    async def _run():
        from app.domains.computer_use.services.customer_loyalty import get_customer_loyalty_engine

        loyalty = get_customer_loyalty_engine()

        sent = 0
        for customer in customers:
            success, seq_id = await loyalty.trigger_welcome_sequence(
                customer_id=customer.get("id", ""),
                customer_name=customer.get("name", ""),
                customer_email=customer.get("email", ""),
                product=customer.get("product", ""),
            )
            if success:
                sent += 1

        logger.info(f"Welcome sequences sent to {sent} customers")
        return {"status": "success", "sent": sent}

    try:
        return asyncio.run(_run())
    except Exception as exc:
        logger.error(f"Error in welcome sequences: {exc}")
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


@shared_task(bind=True, max_retries=2, default_retry_delay=600)
def send_upsell_campaigns(self) -> Dict[str, Any]:
    """
    Fase 12: Envía upsells automáticos a clientes.

    Corre cada 7 días para clientes activos.
    """
    async def _run():
        from app.domains.computer_use.services.customer_loyalty import get_customer_loyalty_engine

        loyalty = get_customer_loyalty_engine()

        # Mock: obtener clientes elegibles para upsell
        customers = []  # En prod: consultar DB

        sent = 0
        for customer in customers:
            opportunity = await loyalty.create_upsell_offer(
                customer_id=customer.get("id", ""),
                product_purchased=customer.get("product", ""),
                upsell_product="Premium",
            )

            success = await loyalty.send_upsell_email(
                opportunity=opportunity,
                customer_email=customer.get("email", ""),
                customer_name=customer.get("name", ""),
            )

            if success:
                sent += 1

        logger.info(f"Upsells sent to {sent} customers")
        return {"status": "success", "upsells_sent": sent}

    try:
        return asyncio.run(_run())
    except Exception as exc:
        logger.error(f"Error in upsells: {exc}")
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


@shared_task(bind=True, max_retries=1, default_retry_delay=600)
def send_winback_campaigns(self) -> Dict[str, Any]:
    """
    Fase 12: Detecta clientes at-risk + envía win-back.

    Corre cada 14 días.
    """
    async def _run():
        from app.domains.computer_use.services.customer_loyalty import get_customer_loyalty_engine

        loyalty = get_customer_loyalty_engine()

        # Mock: obtener at-risk customers
        at_risk = []  # En prod: consultar DB (inactivos 30+ días)

        stats = await loyalty.send_win_back_campaign(at_risk)

        logger.info(f"Win-back campaign: {stats['sent']} sent")
        return {"status": "success", **stats}

    try:
        return asyncio.run(_run())
    except Exception as exc:
        logger.error(f"Error in win-back: {exc}")
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


@shared_task(bind=True, max_retries=1)
def daily_growth_cycle(self, product_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fase 10: Ciclo diario de crecimiento (trending → content → publish).

    Corre diariamente a las 6 AM UTC.
    """
    async def _run():
        from app.domains.computer_use.services.growth_automation_engine import get_growth_automation_engine

        growth = get_growth_automation_engine()

        result = await growth.run_daily_growth_cycle(
            platform="instagram",
            account_id="default",
            product_info=product_info,
        )

        logger.info(f"Daily growth cycle completed: {result}")
        return result

    try:
        return asyncio.run(_run())
    except Exception as exc:
        logger.error(f"Error in growth cycle: {exc}")
        raise self.retry(exc=exc, countdown=3600)  # Retry en 1 hora


# Celery Beat Schedules (periodic tasks)
def setup_periodic_tasks(sender, **kwargs):
    """Configura tasks periódicas en Celery Beat."""

    # Diariamente 9 AM: follow-ups (senior-salesperson cadence, not just Mondays)
    sender.add_periodic_task(
        crontab(hour=9, minute=0),
        send_follow_ups.s(),
        name="Send follow-ups",
    )

    # Cada 7 días: envía upsells
    sender.add_periodic_task(
        crontab(hour=10, minute=0, day_of_week=2),  # Martes 10 AM
        send_upsell_campaigns.s(),
        name="Send upsells",
    )

    # Cada 14 días: win-back
    sender.add_periodic_task(
        crontab(hour=11, minute=0, day_of_week=3),  # Miércoles 11 AM
        send_winback_campaigns.s(),
        name="Send win-back campaigns",
    )

    # Diariamente 6 AM UTC: growth cycle
    sender.add_periodic_task(
        crontab(hour=6, minute=0),
        daily_growth_cycle.s({"name": "SellIA Pro", "price": 499}),
        name="Daily growth cycle",
    )


# Import crontab
from celery.schedules import crontab
