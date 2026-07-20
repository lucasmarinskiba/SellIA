"""A/B Testing Service

Core engine for running prompt experiments: variant assignment,
result recording, and statistical analysis.
"""

import uuid
import math
import hashlib
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.domains.agents.ab_testing import PromptExperiment, PromptExperimentResult

logger = get_logger(__name__)


class ABTestEngine:
    """Service for managing A/B prompt experiments."""

    # ------------------------------------------------------------------
    # Experiment CRUD
    # ------------------------------------------------------------------

    @staticmethod
    async def create_experiment(
        db: AsyncSession,
        name: str,
        agent_type: str,
        variant_a_name: str,
        variant_a_prompt: str,
        variant_b_name: str,
        variant_b_prompt: str,
        metric: str = "conversion",
        business_id: Optional[uuid.UUID] = None,
        confidence_threshold: float = 0.95,
        min_samples: int = 100,
    ) -> PromptExperiment:
        """Create a new prompt experiment."""
        experiment = PromptExperiment(
            business_id=business_id,
            name=name,
            agent_type=agent_type,
            metric=metric,
            variant_a_name=variant_a_name,
            variant_a_prompt=variant_a_prompt,
            variant_b_name=variant_b_name,
            variant_b_prompt=variant_b_prompt,
            status="draft",
            confidence_threshold=confidence_threshold,
            min_samples=min_samples,
        )
        db.add(experiment)
        await db.commit()
        await db.refresh(experiment)
        logger.info(f"Created experiment {experiment.id} for agent '{agent_type}'")
        return experiment

    @staticmethod
    async def get_experiment(
        db: AsyncSession,
        experiment_id: uuid.UUID,
    ) -> Optional[PromptExperiment]:
        """Fetch a single experiment by ID."""
        result = await db.execute(
            select(PromptExperiment).where(PromptExperiment.id == experiment_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_active_experiment_for_agent(
        db: AsyncSession,
        agent_type: str,
        business_id: Optional[uuid.UUID] = None,
    ) -> Optional[PromptExperiment]:
        """Return the first running experiment for the given agent type."""
        filters = [
            PromptExperiment.agent_type == agent_type,
            PromptExperiment.status == "running",
        ]
        if business_id is not None:
            filters.append(PromptExperiment.business_id == business_id)
        else:
            filters.append(PromptExperiment.business_id.is_(None))

        result = await db.execute(
            select(PromptExperiment)
            .where(and_(*filters))
            .order_by(PromptExperiment.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_experiments(
        db: AsyncSession,
        status: Optional[str] = None,
        business_id: Optional[uuid.UUID] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """List experiments with optional filters."""
        query = select(PromptExperiment)
        count_query = select(func.count(PromptExperiment.id))

        filters = []
        if status:
            filters.append(PromptExperiment.status == status)
        if business_id is not None:
            filters.append(PromptExperiment.business_id == business_id)

        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))

        query = query.order_by(PromptExperiment.created_at.desc()).limit(limit).offset(offset)

        result = await db.execute(query)
        experiments = result.scalars().all()

        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        return {"total": total, "experiments": list(experiments)}

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    @staticmethod
    async def start_experiment(
        db: AsyncSession,
        experiment_id: uuid.UUID,
    ) -> PromptExperiment:
        """Move experiment from draft/paused to running."""
        experiment = await ABTestEngine.get_experiment(db, experiment_id)
        if not experiment:
            raise ValueError("Experiment not found")
        if experiment.status not in ("draft", "paused"):
            raise ValueError(f"Cannot start experiment in status '{experiment.status}'")

        experiment.status = "running"
        experiment.started_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(experiment)
        logger.info(f"Started experiment {experiment_id}")
        return experiment

    @staticmethod
    async def pause_experiment(
        db: AsyncSession,
        experiment_id: uuid.UUID,
    ) -> PromptExperiment:
        """Pause a running experiment."""
        experiment = await ABTestEngine.get_experiment(db, experiment_id)
        if not experiment:
            raise ValueError("Experiment not found")
        if experiment.status != "running":
            raise ValueError(f"Cannot pause experiment in status '{experiment.status}'")

        experiment.status = "paused"
        await db.commit()
        await db.refresh(experiment)
        logger.info(f"Paused experiment {experiment_id}")
        return experiment

    @staticmethod
    async def complete_experiment(
        db: AsyncSession,
        experiment_id: uuid.UUID,
        winner: Optional[str] = None,
    ) -> PromptExperiment:
        """Mark experiment as completed with optional winner."""
        experiment = await ABTestEngine.get_experiment(db, experiment_id)
        if not experiment:
            raise ValueError("Experiment not found")

        experiment.status = "completed"
        experiment.winner_variant = winner
        experiment.completed_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(experiment)
        logger.info(f"Completed experiment {experiment_id} with winner={winner}")
        return experiment

    @staticmethod
    async def promote_experiment(
        db: AsyncSession,
        experiment_id: uuid.UUID,
        variant: str,
    ) -> PromptExperiment:
        """Manually promote a variant and close the experiment."""
        experiment = await ABTestEngine.get_experiment(db, experiment_id)
        if not experiment:
            raise ValueError("Experiment not found")
        if variant not in ("a", "b"):
            raise ValueError("Variant must be 'a' or 'b'")

        experiment.status = "auto_promoted"
        experiment.winner_variant = variant
        experiment.completed_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(experiment)
        logger.info(f"Promoted variant '{variant}' for experiment {experiment_id}")
        return experiment

    # ------------------------------------------------------------------
    # Variant assignment
    # ------------------------------------------------------------------

    @staticmethod
    def get_variant_for_conversation(
        db: AsyncSession,
        experiment_id: uuid.UUID,
        conversation_id: uuid.UUID,
    ) -> str:
        """Deterministic 50/50 split using hash of conversation_id + experiment_id."""
        key = f"{str(conversation_id)}:{str(experiment_id)}"
        digest = hashlib.sha256(key.encode()).hexdigest()
        # Use first 8 hex chars as int, even split
        val = int(digest[:8], 16)
        return "a" if val % 2 == 0 else "b"

    # ------------------------------------------------------------------
    # Results
    # ------------------------------------------------------------------

    @staticmethod
    async def record_result(
        db: AsyncSession,
        experiment_id: uuid.UUID,
        conversation_id: uuid.UUID,
        variant: str,
        outcome: Optional[str] = None,
        revenue: Optional[float] = None,
        engagement_score: Optional[float] = None,
    ) -> PromptExperimentResult:
        """Record the outcome of a conversation for an experiment."""
        result = PromptExperimentResult(
            experiment_id=experiment_id,
            variant=variant,
            conversation_id=conversation_id,
            outcome=outcome,
            revenue=revenue,
            engagement_score=engagement_score,
        )
        db.add(result)
        await db.commit()
        await db.refresh(result)
        logger.info(
            f"Recorded result for experiment {experiment_id} "
            f"variant={variant} conversation={conversation_id}"
        )
        return result

    @staticmethod
    async def get_results(
        db: AsyncSession,
        experiment_id: uuid.UUID,
        variant: Optional[str] = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> List[PromptExperimentResult]:
        """Fetch raw results for an experiment."""
        query = select(PromptExperimentResult).where(
            PromptExperimentResult.experiment_id == experiment_id
        )
        if variant:
            query = query.where(PromptExperimentResult.variant == variant)
        query = query.order_by(PromptExperimentResult.created_at.desc()).limit(limit).offset(offset)
        result = await db.execute(query)
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Analysis
    # ------------------------------------------------------------------

    @staticmethod
    async def analyze_experiment(
        db: AsyncSession,
        experiment_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """Compute conversion rates, z-score, p-value, and determine winner."""
        experiment = await ABTestEngine.get_experiment(db, experiment_id)
        if not experiment:
            raise ValueError("Experiment not found")

        # Aggregate counts per variant
        stmt = (
            select(
                PromptExperimentResult.variant,
                func.count(PromptExperimentResult.id).label("n"),
                func.sum(
                    func.case(
                        (PromptExperimentResult.outcome.in_(
                            ["lead_generated", "sale_closed", "objection_overcome", "converted"]
                        ), 1),
                        else_=0,
                    )
                ).label("conversions"),
            )
            .where(PromptExperimentResult.experiment_id == experiment_id)
            .group_by(PromptExperimentResult.variant)
        )
        result = await db.execute(stmt)
        rows = {r.variant: {"n": r.n, "conversions": r.conversions or 0} for r in result.all()}

        n_a = rows.get("a", {}).get("n", 0)
        n_b = rows.get("b", {}).get("n", 0)
        conv_a = rows.get("a", {}).get("conversions", 0)
        conv_b = rows.get("b", {}).get("conversions", 0)

        rate_a = conv_a / n_a if n_a > 0 else 0.0
        rate_b = conv_b / n_b if n_b > 0 else 0.0

        # Z-test for two proportions
        z = 0.0
        p_value = 1.0
        if n_a > 0 and n_b > 0:
            p1 = conv_a / n_a
            p2 = conv_b / n_b
            p = (conv_a + conv_b) / (n_a + n_b)
            se = math.sqrt(p * (1 - p) * (1 / n_a + 1 / n_b))
            z = (p1 - p2) / se if se > 0 else 0.0
            # Two-tailed p-value
            p_value = 2 * (1 - ABTestEngine._normal_cdf(abs(z)))

        winner = None
        if p_value < (1 - experiment.confidence_threshold):
            if rate_a > rate_b:
                winner = "a"
            elif rate_b > rate_a:
                winner = "b"
            else:
                winner = "tie"

        is_significant = p_value < (1 - experiment.confidence_threshold)

        return {
            "experiment_id": experiment_id,
            "n_a": n_a,
            "n_b": n_b,
            "conversions_a": conv_a,
            "conversions_b": conv_b,
            "rate_a": round(rate_a, 4),
            "rate_b": round(rate_b, 4),
            "z_score": round(z, 4),
            "p_value": round(p_value, 6),
            "winner": winner,
            "is_significant": is_significant,
        }

    @staticmethod
    def _normal_cdf(x: float) -> float:
        """Approximation of the standard normal CDF."""
        # Abramowitz and Stegun approximation
        b1 = 0.319381530
        b2 = -0.356563782
        b3 = 1.781477937
        b4 = -1.821255978
        b5 = 1.330274429
        p = 0.2316419
        c = 0.39894228

        if x >= 0.0:
            t = 1.0 / (1.0 + p * x)
            return 1.0 - c * math.exp(-x * x / 2.0) * t * (
                t * (t * (t * (t * b5 + b4) + b3) + b2) + b1
            )
        else:
            return 1.0 - ABTestEngine._normal_cdf(-x)

    @staticmethod
    async def check_auto_promote(
        db: AsyncSession,
        experiment_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """Auto-promote if significant and min_samples reached."""
        experiment = await ABTestEngine.get_experiment(db, experiment_id)
        if not experiment:
            raise ValueError("Experiment not found")

        analysis = await ABTestEngine.analyze_experiment(db, experiment_id)
        n_total = analysis["n_a"] + analysis["n_b"]

        can_promote = (
            analysis["is_significant"]
            and n_total >= experiment.min_samples
            and experiment.status == "running"
        )

        if can_promote and analysis.get("winner") in ("a", "b"):
            await ABTestEngine.promote_experiment(db, experiment_id, analysis["winner"])
            analysis["auto_promoted"] = True
            analysis["promoted_variant"] = analysis["winner"]
        else:
            analysis["auto_promoted"] = False
            analysis["promoted_variant"] = None

        analysis["samples"] = n_total
        analysis["min_samples"] = experiment.min_samples
        return analysis
