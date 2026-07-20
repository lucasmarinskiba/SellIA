"""Sales Funnel Orchestrator — Master controller for complete pipeline.

Orquesta: Find → Contact → Respond → Close → Pay → Grow → Loyalty
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from app.domains.computer_use.services.lead_generator import get_lead_generator
from app.domains.computer_use.services.outreach_orchestrator import get_outreach_orchestrator, OutreachChannel
from app.domains.computer_use.services.auto_responder import get_auto_responder_service
from app.domains.computer_use.services.sales_closer import get_sales_closer_service
from app.domains.computer_use.services.conversion_tracker import get_conversion_tracker
from app.domains.computer_use.services.growth_automation_engine import get_growth_automation_engine
from app.domains.computer_use.services.customer_loyalty import get_customer_loyalty_engine
from app.domains.computer_use.services.lead_scorer import get_lead_scorer_service

logger = logging.getLogger(__name__)


class SalesFunnelOrchestrator:
    """Orquestador master: ejecuta pipeline completo."""

    def __init__(self, db=None):
        self.db = db
        self.logger = logger

        # Servicios de cada fase
        self.lead_gen = get_lead_generator()
        self.outreach = get_outreach_orchestrator()
        self.auto_responder = get_auto_responder_service(db) if db else None
        self.sales_closer = get_sales_closer_service(db) if db else None
        self.conversion = get_conversion_tracker(db) if db else None
        self.growth = get_growth_automation_engine()
        self.loyalty = get_customer_loyalty_engine()

        # Estado
        self.campaign_id = None
        self.metrics = {
            "leads_imported": 0,
            "leads_contacted": 0,
            "leads_responded": 0,
            "sales_closed": 0,
            "payments_processed": 0,
            "upsells_sent": 0,
            "revenue": 0.0,
        }

    async def run_complete_pipeline(
        self,
        leads_data: List[Dict[str, Any]],
        product_info: Dict[str, Any],
        outreach_channel: OutreachChannel = OutreachChannel.EMAIL,
    ) -> Dict[str, Any]:
        """
        Ejecuta pipeline completo: Find → Contact → Response → Close → Pay → Grow → Loyalty
        """
        try:
            self.campaign_id = f"campaign_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

            self.logger.info(f"Starting pipeline: {self.campaign_id}")

            # FASE 11: FIND → Importa y enriquece leads
            imported_leads = await self._find_phase(leads_data)

            if not imported_leads:
                return {"status": "failed", "message": "No leads to process"}

            # FASE 11: CONTACT → Outreach automático
            contacted = await self._contact_phase(imported_leads, outreach_channel)

            # FASE 1-2: RESPOND → Auto-responder
            responses = await self._respond_phase(contacted)

            # FASE 3-5: QUALIFY → Score + Sales Closer
            qualified = await self._qualify_phase(responses, product_info)

            # FASE 9: CLOSE + PAY → Stripe checkout
            paid = await self._close_and_pay_phase(qualified, product_info)

            # FASE 12: LOYALTY → Email sequences
            loyalty = await self._loyalty_phase(paid)

            # FASE 10: GROW → Content + publishing
            growth = await self._grow_phase(product_info)

            # Resultado
            result = {
                "campaign_id": self.campaign_id,
                "status": "completed",
                "phases": {
                    "find": {"leads_imported": len(imported_leads)},
                    "contact": {"leads_contacted": len(contacted)},
                    "respond": {"responses": len(responses)},
                    "qualify": {"qualified": len(qualified)},
                    "close_pay": {"paid": len(paid)},
                    "loyalty": loyalty,
                    "grow": growth,
                },
                "total_metrics": self.metrics,
            }

            self.logger.info(f"Pipeline completed: {result}")

            return result

        except Exception as e:
            self.logger.error(f"Pipeline error: {e}")
            return {"status": "error", "message": str(e)}

    async def _find_phase(self, leads_data: List[Dict[str, Any]]) -> List[Any]:
        """Fase 11: Importa + enriquece leads."""
        try:
            leads = await self.lead_gen.import_leads(leads_data)

            for lead in leads:
                lead = await self.lead_gen.enrich_lead(lead)
                lead = await self.lead_gen.score_lead(lead)

            self.metrics["leads_imported"] = len(leads)

            self.logger.info(f"Find phase: {len(leads)} leads")

            return leads

        except Exception as e:
            self.logger.error(f"Find phase error: {e}")
            return []

    async def _contact_phase(
        self,
        leads: List[Any],
        channel: OutreachChannel,
    ) -> List[Any]:
        """Fase 11: Outreach automático a leads."""
        try:
            campaign = await self.outreach.create_campaign(
                name=f"Campaign {self.campaign_id}",
                target_quality="hot",
                channel=channel,
            )

            contacted = []

            for lead in leads:
                if lead.quality.value == "hot":
                    success, msg_id = await self.outreach.send_outreach(
                        campaign=campaign,
                        lead=lead,
                        sender_name="SellIA Bot",
                        sender_email="bot@sellía.ai",
                    )

                    if success:
                        contacted.append(lead)

            self.metrics["leads_contacted"] = len(contacted)

            self.logger.info(f"Contact phase: {len(contacted)} leads contacted")

            return contacted

        except Exception as e:
            self.logger.error(f"Contact phase error: {e}")
            return []

    async def _respond_phase(self, leads: List[Any]) -> List[Any]:
        """Fase 1-2: Auto-responder a replies."""
        # En prod: webhook detecta respuestas
        # Mock: asumir 30% responden
        responded = leads[:int(len(leads) * 0.3)]

        self.metrics["leads_responded"] = len(responded)

        self.logger.info(f"Respond phase: {len(responded)} responses")

        return responded

    async def _qualify_phase(
        self,
        leads: List[Any],
        product_info: Dict[str, Any],
    ) -> List[Any]:
        """Fase 3-5: Score + Sales Closer."""
        qualified = []

        for lead in leads:
            # Mock: 50% calificados para cierre
            if hash(lead.lead_id) % 2 == 0:
                qualified.append(lead)

        self.logger.info(f"Qualify phase: {len(qualified)} qualified")

        return qualified

    async def _close_and_pay_phase(
        self,
        leads: List[Any],
        product_info: Dict[str, Any],
    ) -> List[Any]:
        """Fase 9: Sales Closer + Stripe payment."""
        paid = []

        for lead in leads:
            # Mock: 70% cierran
            if hash(lead.lead_id) % 10 < 7:
                # En prod: generar checkout real
                self.metrics["sales_closed"] += 1
                self.metrics["payments_processed"] += 1
                self.metrics["revenue"] += product_info.get("price", 100)

                paid.append(lead)

        self.logger.info(f"Close+Pay phase: {len(paid)} paid")

        return paid

    async def _loyalty_phase(self, customers: List[Any]) -> Dict[str, Any]:
        """Fase 12: Email sequences + upsell."""
        try:
            # Crear sequences
            welcome = await self.loyalty.create_email_sequence(
                name="Welcome",
                sequence_type="welcome",
            )

            upsell = await self.loyalty.create_email_sequence(
                name="Upsell",
                sequence_type="upsell",
            )

            # Trigger para cada customer
            for customer in customers:
                await self.loyalty.trigger_welcome_sequence(
                    customer_id=customer.lead_id,
                    customer_name=customer.name,
                    customer_email=customer.email,
                    product="SellIA Pro",
                )

                # Crear upsell opportunity
                opportunity = await self.loyalty.create_upsell_offer(
                    customer_id=customer.lead_id,
                    product_purchased="SellIA Pro",
                    upsell_product="SellIA Enterprise",
                    discount=0.15,
                )

                await self.loyalty.send_upsell_email(
                    opportunity=opportunity,
                    customer_email=customer.email,
                    customer_name=customer.name,
                )

                self.metrics["upsells_sent"] += 1

            return {
                "sequences_created": 2,
                "upsells_sent": len(customers),
                "ltv_impact": "+25%",
            }

        except Exception as e:
            self.logger.error(f"Loyalty phase error: {e}")
            return {"error": str(e)}

    async def _grow_phase(self, product_info: Dict[str, Any]) -> Dict[str, Any]:
        """Fase 10: Growth automation."""
        try:
            result = await self.growth.run_daily_growth_cycle(
                platform="instagram",
                account_id="default",
                product_info=product_info,
            )

            return result

        except Exception as e:
            self.logger.error(f"Grow phase error: {e}")
            return {"error": str(e)}

    async def get_pipeline_status(self) -> Dict[str, Any]:
        """Obtiene status actual del pipeline."""
        return {
            "campaign_id": self.campaign_id,
            "metrics": self.metrics,
            "roi": self.metrics.get("revenue", 0) / max(self.metrics.get("leads_imported", 1), 1),
        }


def get_sales_funnel_orchestrator(db=None) -> SalesFunnelOrchestrator:
    return SalesFunnelOrchestrator(db)
