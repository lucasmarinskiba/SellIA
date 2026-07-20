"""Financial Planner Service"""

import uuid
import json
import csv
import io
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from langchain_core.messages import SystemMessage, HumanMessage

from app.core.logger import get_logger
from app.domains.agents.financial_planner.models import FinancialPlan
from app.domains.agents.llm_provider import generate_with_fallback
from app.domains.agents.prompts.business_context_adapter import (
    get_agent_prompt_context,
    format_business_context_for_prompt,
)

logger = get_logger(__name__)


def _build_financial_prompt(historical_data: Dict[str, Any], assumptions: Dict[str, Any]) -> str:
    return (
        f"Datos históricos (últimos meses):\n"
        f"{json.dumps(historical_data, ensure_ascii=False, indent=2)[:4000]}\n\n"
        f"Supuestos del negocio:\n"
        f"{json.dumps(assumptions, ensure_ascii=False, indent=2)[:2000]}\n\n"
        "Genera proyecciones para los próximos 12 meses."
    )


async def create_financial_plan(
    db: AsyncSession,
    business_id: uuid.UUID,
    plan_name: str,
    historical_data: Dict[str, Any],
    assumptions: Dict[str, Any],
) -> FinancialPlan:
    """Crea un plan financiero con proyecciones LLM + cálculos estadísticos."""
    ctx = await get_agent_prompt_context(db, business_id)
    context_block = format_business_context_for_prompt(ctx)

    system = SystemMessage(
        content=(
            "Eres un CFO experto en startups y PYMES. Genera un plan financiero en español "
            "personalizado para el negocio del cliente. "
            "Devuelve SOLO un JSON válido con esta estructura exacta:\n"
            '{"revenue_projections": [{"month": 1, "amount": 0.0}, ...], '
            '"expense_projections": [{"month": 1, "amount": 0.0}, ...], '
            '"cash_flow": [{"month": 1, "inflow": 0.0, "outflow": 0.0, "net": 0.0}, ...], '
            '"break_even_month": 0, '
            '"scenarios": {'
            '"optimistic": {"monthly_data": [...], "total_revenue": 0.0, "total_expense": 0.0, "net_result": 0.0}, '
            '"base": {"monthly_data": [...], "total_revenue": 0.0, "total_expense": 0.0, "net_result": 0.0}, '
            '"pessimistic": {"monthly_data": [...], "total_revenue": 0.0, "total_expense": 0.0, "net_result": 0.0}'
            '}, '
            '"metrics": {"ltv": 0.0, "cac": 0.0, "runway_months": 0, "ltv_cac_ratio": 0.0}}\n'
            "Los montos deben ser números (float). Incluye exactamente 12 meses."
        )
    )
    human_content = _build_financial_prompt(historical_data, assumptions)
    if context_block:
        human_content = f"{context_block}\n\n{human_content}"
    human = HumanMessage(content=human_content)

    response = await generate_with_fallback(
        db=db,
        business_id=business_id,
        messages=[system, human],
        temperature=0.3,
        max_tokens=3000,
    )

    parsed: Dict[str, Any] = {
        "revenue_projections": [],
        "expense_projections": [],
        "cash_flow": [],
        "break_even_month": None,
        "scenarios": {},
        "metrics": {},
    }
    if response:
        try:
            content = response.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            parsed = json.loads(content)
        except Exception as e:
            logger.warning(f"Failed to parse financial plan LLM output: {e}")

    plan = FinancialPlan(
        business_id=business_id,
        plan_name=plan_name,
        revenue_projections=parsed.get("revenue_projections", []),
        expense_projections=parsed.get("expense_projections", []),
        cash_flow=parsed.get("cash_flow", []),
        break_even_month=parsed.get("break_even_month"),
        scenarios=parsed.get("scenarios", {}),
        metrics=parsed.get("metrics", {}),
        assumptions=assumptions,
    )
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return plan


async def get_plan(db: AsyncSession, plan_id: uuid.UUID) -> Optional[FinancialPlan]:
    result = await db.execute(select(FinancialPlan).where(FinancialPlan.id == plan_id))
    return result.scalar_one_or_none()


async def list_plans(db: AsyncSession, business_id: uuid.UUID) -> List[FinancialPlan]:
    result = await db.execute(
        select(FinancialPlan)
        .where(FinancialPlan.business_id == business_id)
        .order_by(desc(FinancialPlan.created_at))
    )
    return result.scalars().all()


async def export_plan(plan: FinancialPlan, format: str = "csv") -> Dict[str, Any]:
    """Exporta el plan a CSV o JSON."""
    if format == "json":
        payload = {
            "plan_id": str(plan.id),
            "plan_name": plan.plan_name,
            "revenue_projections": plan.revenue_projections,
            "expense_projections": plan.expense_projections,
            "cash_flow": plan.cash_flow,
            "break_even_month": plan.break_even_month,
            "scenarios": plan.scenarios,
            "metrics": plan.metrics,
            "assumptions": plan.assumptions,
        }
        return {
            "plan_id": plan.id,
            "format": "json",
            "content": json.dumps(payload, ensure_ascii=False, indent=2),
            "filename": f"financial_plan_{plan.plan_name.replace(' ', '_')}.json",
        }

    # CSV export
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["month", "revenue", "expense", "cash_inflow", "cash_outflow", "cash_net"])
    rev = {r["month"]: r["amount"] for r in plan.revenue_projections}
    exp = {e["month"]: e["amount"] for e in plan.expense_projections}
    cf = {c["month"]: c for c in plan.cash_flow}
    for month in range(1, 13):
        writer.writerow([
            month,
            rev.get(month, 0.0),
            exp.get(month, 0.0),
            cf.get(month, {}).get("inflow", 0.0),
            cf.get(month, {}).get("outflow", 0.0),
            cf.get(month, {}).get("net", 0.0),
        ])
    writer.writerow([])
    writer.writerow(["scenario", "total_revenue", "total_expense", "net_result"])
    for scenario_name, scenario_data in (plan.scenarios or {}).items():
        writer.writerow([
            scenario_name,
            scenario_data.get("total_revenue", 0.0),
            scenario_data.get("total_expense", 0.0),
            scenario_data.get("net_result", 0.0),
        ])
    writer.writerow([])
    writer.writerow(["metric", "value"])
    for k, v in (plan.metrics or {}).items():
        writer.writerow([k, v])

    return {
        "plan_id": plan.id,
        "format": "csv",
        "content": output.getvalue(),
        "filename": f"financial_plan_{plan.plan_name.replace(' ', '_')}.csv",
    }
