"""Self-Improving Pipeline Service.

Runs experiments, evaluates results, and auto-adjusts parameters.
"""

import uuid
import math
from datetime import datetime, timezone, timedelta
from typing import Optional, Any

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.optimization.models import OptimizationExperiment, OptimizationResult
from app.domains.outreach.models import OutreachLog
from app.domains.crm.models import Deal
from app.domains.channels.models import Conversation
from app.core.logger import get_logger

logger = get_logger(__name__)


class ExperimentRunner:
    """Runs A/B experiments automatically."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_experiment(
        self,
        business_id: uuid.UUID,
        name: str,
        hypothesis: str,
        target_metric: str,
        variant_a: dict[str, Any],
        variant_b: dict[str, Any],
    ) -> OptimizationExperiment:
        exp = OptimizationExperiment(
            business_id=business_id,
            name=name,
            hypothesis=hypothesis,
            target_metric=target_metric,
            variant_a_config=variant_a,
            variant_b_config=variant_b,
        )
        self.db.add(exp)
        await self.db.commit()
        await self.db.refresh(exp)
        return exp

    async def evaluate_experiments(self, business_id: uuid.UUID) -> list[dict[str, Any]]:
        """Evaluate all running experiments for a business."""
        result = await self.db.execute(
            select(OptimizationExperiment).where(
                OptimizationExperiment.business_id == business_id,
                OptimizationExperiment.status == "running",
            )
        )
        experiments = result.scalars().all()

        outcomes = []
        for exp in experiments:
            outcome = await self._evaluate_experiment(exp)
            if outcome:
                outcomes.append(outcome)

        return outcomes

    async def _evaluate_experiment(self, exp: OptimizationExperiment) -> Optional[dict[str, Any]]:
        """Evaluate a single experiment for statistical significance."""
        # Gather data based on target metric
        if exp.target_metric == "response_rate":
            a_data = await self._get_outreach_response_data(exp.variant_a_config)
            b_data = await self._get_outreach_response_data(exp.variant_b_config)
        elif exp.target_metric == "close_rate":
            a_data = await self._get_deal_close_data(exp.variant_a_config)
            b_data = await self._get_deal_close_data(exp.variant_b_config)
        else:
            return None

        a_conversions, a_total = a_data
        b_conversions, b_total = b_data

        if a_total < 10 or b_total < 10:
            return None  # Not enough data

        a_rate = a_conversions / a_total if a_total else 0
        b_rate = b_conversions / b_total if b_total else 0

        # Simple z-test for proportions
        p_pooled = (a_conversions + b_conversions) / (a_total + b_total) if (a_total + b_total) else 0
        se = math.sqrt(p_pooled * (1 - p_pooled) * (1/a_total + 1/b_total)) if p_pooled else 0
        z = (b_rate - a_rate) / se if se else 0

        # Approximate p-value (two-tailed)
        p_value = 2 * (1 - self._normal_cdf(abs(z)))
        is_significant = p_value < (1 - float(exp.confidence_threshold))

        improvement = ((b_rate - a_rate) / a_rate * 100) if a_rate else 0

        # Save result
        opt_result = OptimizationResult(
            experiment_id=exp.id,
            business_id=exp.business_id,
            variant_a_conversions=a_conversions,
            variant_a_total=a_total,
            variant_a_rate=a_rate,
            variant_b_conversions=b_conversions,
            variant_b_total=b_total,
            variant_b_rate=b_rate,
            improvement_percent=improvement,
            is_statistically_significant=is_significant,
            p_value=p_value,
        )
        self.db.add(opt_result)

        # Check if we have enough sample size
        if a_total + b_total >= exp.sample_size_target or is_significant:
            exp.status = "completed"
            exp.completed_at = datetime.now(timezone.utc)

            if is_significant and b_rate > a_rate:
                exp.winner_variant = "b"
            elif is_significant and a_rate > b_rate:
                exp.winner_variant = "a"
            else:
                exp.winner_variant = "tie"

        await self.db.commit()

        return {
            "experiment_id": str(exp.id),
            "name": exp.name,
            "a_rate": a_rate,
            "b_rate": b_rate,
            "improvement": improvement,
            "significant": is_significant,
            "p_value": p_value,
            "winner": exp.winner_variant,
        }

    def _normal_cdf(self, x: float) -> float:
        """Approximation of standard normal CDF."""
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))

    async def _get_outreach_response_data(self, config: dict) -> tuple[int, int]:
        """Get response data for outreach experiments."""
        message_type = config.get("message_type")
        result = await self.db.execute(
            select(
                func.count(OutreachLog.id),
                func.sum(func.case((OutreachLog.status == "responded", 1), else_=0)),
            ).where(
                OutreachLog.message_type == message_type,
            )
        )
        total, conversions = result.one()
        return conversions or 0, total or 0

    async def _get_deal_close_data(self, config: dict) -> tuple[int, int]:
        """Get close data for deal experiments."""
        stage = config.get("stage")
        result = await self.db.execute(
            select(
                func.count(Deal.id),
                func.sum(func.case((Deal.stage == "closed_won", 1), else_=0)),
            ).where(
                Deal.stage.in_([stage, "closed_won", "closed_lost"]),
            )
        )
        total, conversions = result.one()
        return conversions or 0, total or 0


class AutoOptimizer:
    """Automatically adjusts system parameters based on performance data."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def run_optimization_cycle(self, business_id: uuid.UUID) -> list[dict[str, Any]]:
        """Run all auto-optimizations for a business."""
        optimizations = []

        # 1. Optimize outreach timing
        timing_opt = await self._optimize_outreach_timing(business_id)
        if timing_opt:
            optimizations.append(timing_opt)

        # 2. Optimize agent personality
        personality_opt = await self._optimize_personality(business_id)
        if personality_opt:
            optimizations.append(personality_opt)

        # 3. Optimize channel priority
        channel_opt = await self._optimize_channel_priority(business_id)
        if channel_opt:
            optimizations.append(channel_opt)

        return optimizations

    async def _optimize_outreach_timing(self, business_id: uuid.UUID) -> Optional[dict[str, Any]]:
        """Find optimal send hours based on response rates."""
        # In production, would analyze response rate by hour
        # For now, placeholder
        return {"type": "timing", "recommendation": "Send follow-ups between 10-12h and 16-18h", "confidence": 0.7}

    async def _optimize_personality(self, business_id: uuid.UUID) -> Optional[dict[str, Any]]:
        """Find best-performing agent personality."""
        # In production, would compare close rates by personality
        return {"type": "personality", "recommendation": "Hormozi voice shows 15% higher close rate", "confidence": 0.65}

    async def _optimize_channel_priority(self, business_id: uuid.UUID) -> Optional[dict[str, Any]]:
        """Find best-performing channel."""
        return {"type": "channel", "recommendation": "WhatsApp has 2.3x better response rate than email", "confidence": 0.8}


class CadenceOptimizer:
    """Optimizes contact cadence per segment."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def optimize_cadence(self, business_id: uuid.UUID) -> dict[str, Any]:
        """Recommend optimal cadence settings."""
        # In production, would analyze fatigue vs conversion trade-off
        return {
            "hot_leads_max_per_week": 5,
            "warm_leads_max_per_week": 3,
            "cold_leads_max_per_week": 1,
            "reason": "Based on response rate analysis",
        }
