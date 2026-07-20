"""Acquisition Strategist Service"""

import uuid
import json
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from langchain_core.messages import SystemMessage, HumanMessage

from app.core.logger import get_logger
from app.domains.agents.acquisition_strategist.models import AcquisitionStrategy
from app.domains.agents.llm_provider import generate_with_fallback
from app.domains.agents.prompts.business_context_adapter import (
    get_agent_prompt_context,
    format_business_context_for_prompt,
)

logger = get_logger(__name__)


async def design_acquisition_strategy(
    db: AsyncSession,
    business_id: uuid.UUID,
    strategy_name: str,
    goals: Dict[str, Any],
    budget: Optional[float],
) -> AcquisitionStrategy:
    """Diseña una estrategia de adquisición completa usando LLM."""
    ctx = await get_agent_prompt_context(db, business_id)
    context_block = format_business_context_for_prompt(ctx)

    system = SystemMessage(
        content=(
            "Eres un growth hacker senior especializado en adquisición de clientes. "
            "Diseña una estrategia completa en español personalizada para el negocio del cliente. "
            "Devuelve SOLO un JSON válido con esta estructura exacta:\n"
            '{"channels": [{"channel": "organic|paid|referral|partnership|content", '
            '"budget_pct": 0.0, "expected_cac": 0.0, "expected_volume": 0, "tactics": ["..."]}], '
            '"funnel_stages": [{"stage": "awareness|interest|decision|action", '
            '"conversion_rate": 0.0, "actions": ["..."]}], '
            '"cac_target": 0.0, "ltv_target": 0.0, '
            '"sequences": [{"type": "email|ad|whatsapp", "channel": "...", '
            '"steps": [{"step": 1, "content": "...", "delay_hours": 0}]}], '
            '"budget_allocation": {"organic": 0.0, "paid": 0.0, "referral": 0.0, "partnership": 0.0, "content": 0.0}, '
            '"expected_results": {"total_customers": 0, "total_revenue": 0.0, "roi_estimate": 0.0}}'
        )
    )
    human_content = (
        f"Objetivos: {json.dumps(goals, ensure_ascii=False, indent=2)}\n"
        f"Presupuesto mensual estimado: {budget if budget is not None else 'No especificado'}\n"
        "Diseña la estrategia óptima para este negocio."
    )
    if context_block:
        human_content = f"{context_block}\n\n{human_content}"
    human = HumanMessage(content=human_content)

    response = await generate_with_fallback(
        db=db,
        business_id=business_id,
        messages=[system, human],
        temperature=0.4,
        max_tokens=3000,
    )

    parsed: Dict[str, Any] = {
        "channels": [],
        "funnel_stages": [],
        "cac_target": None,
        "ltv_target": None,
        "sequences": [],
        "budget_allocation": {},
        "expected_results": {},
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
            logger.warning(f"Failed to parse acquisition strategy LLM output: {e}")

    strategy = AcquisitionStrategy(
        business_id=business_id,
        strategy_name=strategy_name,
        channels=parsed.get("channels", []),
        funnel_stages=parsed.get("funnel_stages", []),
        cac_target=parsed.get("cac_target"),
        ltv_target=parsed.get("ltv_target"),
        sequences=parsed.get("sequences", []),
        budget_allocation=parsed.get("budget_allocation", {}),
        expected_results=parsed.get("expected_results", {}),
    )
    db.add(strategy)
    await db.commit()
    await db.refresh(strategy)
    return strategy


async def get_strategy(db: AsyncSession, strategy_id: uuid.UUID) -> Optional[AcquisitionStrategy]:
    result = await db.execute(select(AcquisitionStrategy).where(AcquisitionStrategy.id == strategy_id))
    return result.scalar_one_or_none()


async def list_strategies(db: AsyncSession, business_id: uuid.UUID) -> List[AcquisitionStrategy]:
    result = await db.execute(
        select(AcquisitionStrategy)
        .where(AcquisitionStrategy.business_id == business_id)
        .order_by(desc(AcquisitionStrategy.created_at))
    )
    return result.scalars().all()
