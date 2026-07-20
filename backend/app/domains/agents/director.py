"""SellIA Director — CEO IA / Meta-Agent Orchestrator.

The SellIA Director is the virtual CEO that coordinates all departments,
monitors objectives, evaluates KPIs, and takes autonomous strategic actions.
Runs every 6 hours via Celery beat.
"""

import uuid
from typing import Any, Optional, List
from datetime import datetime, timezone, timedelta
from decimal import Decimal

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.objectives.models import BusinessObjective, KPI, ObjectiveStatus
from app.domains.objectives.services import ObjectiveService
from app.domains.analytics.models import InsightAlert
from app.domains.analytics.services import BusinessIntelligenceService
from app.domains.channels.models import Conversation
from app.domains.channels.services import send_outbound_message
from app.domains.agents.ai_reply import generate_raw_ai_response
from app.domains.agents.models import AgentPersonality
from app.core.logger import get_logger

logger = get_logger(__name__)


class SellIADirector:
    """Virtual CEO that orchestrates all AI departments."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.objective_service = ObjectiveService(db)
        self.bi_service = BusinessIntelligenceService(db)

    async def run_director_cycle(self, business_id: uuid.UUID):
        """Execute one full director cycle for a business."""
        logger.info(f"[Director] Starting cycle for business {business_id}")

        # 1. Refresh all KPIs
        await self.objective_service.refresh_all_kpis(business_id)

        # 2. Evaluate objectives
        objectives = await self.objective_service.get_objectives_for_business(business_id, status="active")
        at_risk_objectives = [o for o in objectives if o.status == ObjectiveStatus.AT_RISK]
        missed_objectives = [o for o in objectives if o.status == ObjectiveStatus.MISSED]

        # 3. Detect anomalies
        await self.bi_service.detect_anomalies(business_id)

        # 4. Generate action plan for at-risk objectives
        action_plan = []
        for obj in at_risk_objectives:
            actions = await self._generate_action_plan(obj)
            action_plan.extend(actions)

        # 5. Execute automated actions
        for action in action_plan:
            if action.get("auto_execute"):
                await self._execute_action(business_id, action)

        # 6. Generate Daily Briefing
        briefing = await self._generate_daily_briefing(business_id, objectives, at_risk_objectives, action_plan)

        # 7. Send briefing to business owner if configured
        await self._send_briefing_to_owner(business_id, briefing)

        logger.info(f"[Director] Cycle completed for business {business_id}")
        return {"objectives_evaluated": len(objectives), "at_risk": len(at_risk_objectives), "actions_generated": len(action_plan)}

    async def _generate_action_plan(self, objective: BusinessObjective) -> List[dict[str, Any]]:
        """Generate specific actions to recover an at-risk objective."""
        actions = []
        progress = float(objective.current_value / objective.target_value) if objective.target_value else 0
        gap = float(objective.target_value - objective.current_value) if objective.target_value else 0

        # Days remaining
        days_remaining = (objective.end_date - datetime.now(timezone.utc)).days if objective.end_date else 30
        if days_remaining <= 0:
            days_remaining = 1

        daily_needed = gap / days_remaining

        if objective.linked_channel_platform:
            actions.append({
                "type": "increase_channel_activity",
                "channel": objective.linked_channel_platform,
                "message": f"Aumentar actividad en {objective.linked_channel_platform} para alcanzar meta",
                "auto_execute": False,
                "priority": "high",
            })

        if progress < 0.5 and days_remaining < 15:
            actions.append({
                "type": "launch_recovery_campaign",
                "message": f"Lanzar campaña de recovery: faltan {gap} unidades en {days_remaining} días",
                "auto_execute": True,
                "priority": "critical",
                "workflow_type": "re_engagement",
            })

        if "revenue" in objective.name.lower() or objective.unit in ("ARS", "USD"):
            actions.append({
                "type": "activate_upsell",
                "message": "Activar workflows de upsell/cross-sell a clientes existentes",
                "auto_execute": True,
                "priority": "high",
            })

        return actions

    async def _execute_action(self, business_id: uuid.UUID, action: dict[str, Any]):
        """Execute an automated action."""
        try:
            if action["type"] == "launch_recovery_campaign":
                # Find or create a recovery workflow
                from app.domains.automations.models import Workflow, WorkflowTriggerType, WorkflowStatus
                result = await self.db.execute(
                    select(Workflow).where(
                        Workflow.business_id == business_id,
                        Workflow.name.ilike("%recovery%"),
                        Workflow.is_active == True,
                    )
                )
                workflow = result.scalar_one_or_none()
                if workflow and workflow.status == WorkflowStatus.PAUSED:
                    workflow.status = WorkflowStatus.ACTIVE
                    await self.db.commit()
                    logger.info(f"[Director] Activated recovery workflow for business {business_id}")

            elif action["type"] == "activate_upsell":
                from app.domains.automations.models import Workflow, WorkflowStatus
                result = await self.db.execute(
                    select(Workflow).where(
                        Workflow.business_id == business_id,
                        Workflow.name.ilike("%upsell%"),
                        Workflow.is_active == True,
                    )
                )
                workflow = result.scalar_one_or_none()
                if workflow and workflow.status == WorkflowStatus.PAUSED:
                    workflow.status = WorkflowStatus.ACTIVE
                    await self.db.commit()
                    logger.info(f"[Director] Activated upsell workflow for business {business_id}")

        except Exception as e:
            logger.error(f"[Director] Action execution error: {e}")

    async def _generate_daily_briefing(self, business_id: uuid.UUID, objectives: List[BusinessObjective], at_risk: List[BusinessObjective], action_plan: List[dict]) -> str:
        """Generate an AI-powered daily briefing for the business owner."""
        # Gather context
        total_objectives = len(objectives)
        achieved = sum(1 for o in objectives if o.status == ObjectiveStatus.ACHIEVED)
        at_risk_count = len(at_risk)

        # Recent insights
        insights_result = await self.db.execute(
            select(InsightAlert).where(
                InsightAlert.business_id == business_id,
                InsightAlert.created_at >= datetime.now(timezone.utc) - timedelta(hours=24),
            ).order_by(desc(InsightAlert.created_at)).limit(5)
        )
        insights = insights_result.scalars().all()

        # Build context for AI
        context = f"""SellIA Daily Briefing para el dueño del negocio:

OBJETIVOS DEL PERÍODO:
- Total activos: {total_objectives}
- Logrados: {achieved}
- En riesgo: {at_risk_count}

OBJETIVOS EN RIESGO:
"""
        for obj in at_risk:
            progress = float(obj.current_value / obj.target_value * 100) if obj.target_value else 0
            context += f"- {obj.name}: {obj.current_value}/{obj.target_value} ({progress:.1f}%)\n"

        if insights:
            context += "\nINSIGHTS RECIENTES:\n"
            for ins in insights:
                context += f"- [{ins.severity.upper()}] {ins.title}\n"

        if action_plan:
            context += "\nACCIONES RECOMENDADAS:\n"
            for action in action_plan[:3]:
                context += f"- {action['message']} (prioridad: {action['priority']})\n"

        # Generate AI briefing
        try:
            briefing = await generate_raw_ai_response(
                db=self.db,
                business_id=business_id,
                system_prompt="""Eres el Director General (CEO) de una empresa virtual de ventas y marketing.
Genera un briefing diario conciso y motivador para el dueño del negocio.
Usa tono profesional pero cercano. Máximo 300 palabras.
Incluye:
1. Un resumen ejecutivo de 2-3 líneas
2. Qué objetivos van bien
3. Qué necesita atención
4. Una acción recomendada para hoy
Usa emojis y formato claro.""",
                user_prompt=context,
                max_tokens=800,
                temperature=0.7,
            )
            return briefing or context
        except Exception as e:
            logger.error(f"[Director] Briefing generation error: {e}")
            return context

    async def _send_briefing_to_owner(self, business_id: uuid.UUID, briefing: str):
        """Send the daily briefing to the business owner via their preferred channel."""
        try:
            from app.domains.businesses.models import Business
            result = await self.db.execute(select(Business).where(Business.id == business_id))
            business = result.scalar_one_or_none()
            if not business or not business.owner_id:
                return

            # Find owner's primary conversation (WhatsApp preferred)
            conv_result = await self.db.execute(
                select(Conversation).where(
                    Conversation.business_id == business_id,
                    Conversation.is_active == True,
                ).order_by(desc(Conversation.created_at)).limit(1)
            )
            conv = conv_result.scalar_one_or_none()
            if conv:
                # Send as a message in the conversation thread
                # For now, just log it. In production, this would send via WhatsApp/Email
                logger.info(f"[Director] Briefing ready for business {business_id}: {briefing[:200]}...")

        except Exception as e:
            logger.error(f"[Director] Briefing send error: {e}")


class DirectorTaskRunner:
    """Celery task wrapper for running the director."""

    @staticmethod
    async def run_for_all_businesses():
        """Run director cycle for all active businesses."""
        from app.core.database import AsyncSessionLocal
        from app.domains.businesses.models import Business

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Business).where(Business.is_active == True))
            businesses = result.scalars().all()

            director = SellIADirector(db)
            for business in businesses:
                try:
                    await director.run_director_cycle(business.id)
                except Exception as e:
                    logger.error(f"[DirectorTask] Error for business {business.id}: {e}")

            logger.info(f"[DirectorTask] Completed cycles for {len(businesses)} businesses")
