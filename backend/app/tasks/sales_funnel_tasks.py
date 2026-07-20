"""Celery Tasks — Background automation for sales funnel.

Ejecuta fases en background con retry automático + scheduling.
"""

import logging
from celery import shared_task
from typing import List, Dict, Any
from datetime import datetime, timedelta

from app.domains.computer_use.services.lead_generator import get_lead_generator
from app.domains.computer_use.services.outreach_orchestrator import get_outreach_orchestrator, OutreachChannel
from app.domains.computer_use.services.customer_loyalty import get_customer_loyalty_engine
from app.domains.computer_use.services.growth_automation_engine import get_growth_automation_engine

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def import_and_enrich_leads(self, leads_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Fase 11: Importa + enriquece leads.

    Retries: 3 intentos con delay de 5 minutos.
    """
    try:
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

    except Exception as exc:
        logger.error(f"Error importing leads: {exc}")
        # Retry con backoff exponencial
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
    try:
        lead_gen = get_lead_generator()
        outreach = get_outreach_orchestrator()

        imported = await lead_gen.import_leads(leads)

        # Enrich + score
        for lead in imported:
            lead = await lead_gen.enrich_lead(lead)
            lead = await lead_gen.score_lead(lead)

        # Crear campaign
        campaign = await outreach.create_campaign(
            name=f"Outreach {datetime.utcnow().strftime('%Y%m%d%H%M')}",
            target_quality="hot",
            channel=OutreachChannel(channel),
        )

        # Enviar a HOT
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

    except Exception as exc:
        logger.error(f"Error in outreach: {exc}")
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


@shared_task(bind=True, max_retries=2, default_retry_delay=600)
def send_follow_ups(self) -> Dict[str, Any]:
    """
    Fase 11: Envía follow-ups automáticos.

    Corre cada 3 días para leads que no respondieron.
    """
    try:
        # Mock: obtener leads sin respuesta hace 3 días
        leads_to_followup = []  # En prod: consultar DB

        outreach = get_outreach_orchestrator()

        followup_count = 0
        for lead in leads_to_followup:
            if lead.contacted_count < 3:  # Max 3 intentos
                success, msg_id = await outreach.send_follow_up(
                    campaign=None,  # placeholder
                    lead=lead,
                    follow_up_number=lead.contacted_count + 1,
                )
                if success:
                    followup_count += 1

        logger.info(f"Sent {followup_count} follow-ups")

        return {"status": "success", "followups_sent": followup_count}

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
    try:
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

    except Exception as exc:
        logger.error(f"Error in welcome sequences: {exc}")
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


@shared_task(bind=True, max_retries=2, default_retry_delay=600)
def send_upsell_campaigns(self) -> Dict[str, Any]:
    """
    Fase 12: Envía upsells automáticos a clientes.

    Corre cada 7 días para clientes activos.
    """
    try:
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

    except Exception as exc:
        logger.error(f"Error in upsells: {exc}")
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


@shared_task(bind=True, max_retries=1, default_retry_delay=600)
def send_winback_campaigns(self) -> Dict[str, Any]:
    """
    Fase 12: Detecta clientes at-risk + envía win-back.

    Corre cada 14 días.
    """
    try:
        loyalty = get_customer_loyalty_engine()

        # Mock: obtener at-risk customers
        at_risk = []  # En prod: consultar DB (inactivos 30+ días)

        stats = await loyalty.send_win_back_campaign(at_risk)

        logger.info(f"Win-back campaign: {stats['sent']} sent")

        return {"status": "success", **stats}

    except Exception as exc:
        logger.error(f"Error in win-back: {exc}")
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


@shared_task(bind=True, max_retries=1)
def daily_growth_cycle(self, product_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fase 10: Ciclo diario de crecimiento (trending → content → publish).

    Corre diariamente a las 6 AM UTC.
    """
    try:
        growth = get_growth_automation_engine()

        result = await growth.run_daily_growth_cycle(
            platform="instagram",
            account_id="default",
            product_info=product_info,
        )

        logger.info(f"Daily growth cycle completed: {result}")

        return result

    except Exception as exc:
        logger.error(f"Error in growth cycle: {exc}")
        raise self.retry(exc=exc, countdown=3600)  # Retry en 1 hora


# Celery Beat Schedules (periodic tasks)
def setup_periodic_tasks(sender, **kwargs):
    """Configura tasks periódicas en Celery Beat."""

    # Cada 3 días: envía follow-ups
    sender.add_periodic_task(
        crontab(hour=9, minute=0, day_of_week=1),  # Lunes 9 AM
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
