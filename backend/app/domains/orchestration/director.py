"""SellIA Director — CEO IA that supervises all departments."""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.domains.objectives.models import Department, BusinessObjective, KPI
from app.domains.objectives.services import ObjectiveService
from app.domains.retention.services import RetentionService
from app.domains.finance.services import FinanceService
from app.domains.bi.services import BiService
from app.core.logger import get_logger

logger = get_logger(__name__)


class SellIADirector:
    """Meta-agent that evaluates all departments and generates action plans."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def run_daily_briefing(self, business_id: uuid.UUID) -> dict[str, Any]:
        """Evaluate all KPIs, generate action plans, and return briefing."""
        obj_service = ObjectiveService(self.db)
        objectives = await obj_service.get_objectives_for_business(business_id)
        kpi_status = await self._evaluate_all_kpis(business_id)
        action_plan = await self._generate_action_plan(objectives, kpi_status, business_id)

        return {
            "business_id": str(business_id),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "objectives_count": len(objectives),
            "kpis_evaluated": len(kpi_status),
            "action_plan": action_plan,
        }

    async def _evaluate_all_kpis(self, business_id: uuid.UUID) -> list[dict]:
        result = await self.db.execute(
            select(KPI).where(
                KPI.business_id == business_id,
                KPI.is_active == True,
            )
        )
        kpis = result.scalars().all()
        status = []
        for kpi in kpis:
            target = kpi.target_value or 1
            current = kpi.current_value or 0
            pct = (current / target * 100) if target else 0
            status.append({
                "kpi_id": str(kpi.id),
                "name": kpi.name,
                "target": float(target),
                "current": float(current),
                "percent": float(pct),
                "status": "on_track" if pct >= 80 else "at_risk" if pct >= 50 else "critical",
            })
        return status

    async def _generate_action_plan(
        self,
        objectives: list,
        kpi_status: list[dict],
        business_id: uuid.UUID,
    ) -> list[dict]:
        actions = []
        for kpi in kpi_status:
            if kpi["status"] == "critical":
                actions.append({
                    "priority": "high",
                    "target_kpi": kpi["name"],
                    "action": f"Urgently review {kpi['name']}: currently at {kpi['percent']:.1f}% of target.",
                    "suggested_workflow_adjustment": "Increase automation touchpoints or escalate to human team.",
                })
            elif kpi["status"] == "at_risk":
                actions.append({
                    "priority": "medium",
                    "target_kpi": kpi["name"],
                    "action": f"Monitor {kpi['name']} closely: at {kpi['percent']:.1f}% of target.",
                    "suggested_workflow_adjustment": "A/B test messaging or increase ad spend.",
                })
        if not actions:
            actions.append({
                "priority": "low",
                "target_kpi": "all",
                "action": "All KPIs on track. Consider increasing targets for next period.",
                "suggested_workflow_adjustment": "Run experiments to find new growth levers.",
            })
        return actions

    async def suggest_ab_test_variants(self, business_id: uuid.UUID) -> list[dict]:
        """Suggest A/B test variants based on recent performance."""
        bi_service = BiService(self.db)
        funnel = await bi_service.get_latest_funnel(business_id)
        suggestions = []
        if funnel and funnel.conversion_lead_to_qualified:
            clq = float(funnel.conversion_lead_to_qualified)
            if clq < 30:
                suggestions.append({
                    "test": "lead_qualification_message",
                    "hypothesis": "Changing the first response message will increase qualification rate.",
                    "current_rate": clq,
                })
            if float(funnel.conversion_deal_to_order or 0) < 20:
                suggestions.append({
                    "test": "checkout_urgency",
                    "hypothesis": "Adding scarcity/urgency to closing messages will increase deal-to-order conversion.",
                    "current_rate": float(funnel.conversion_deal_to_order or 0),
                })
        return suggestions
