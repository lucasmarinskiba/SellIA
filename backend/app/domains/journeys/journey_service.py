"""Journey orchestration service."""

import logging
from uuid import UUID
from typing import List, Dict
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.journeys.journey_models import (
    CustomerJourney, JourneyVariant, JourneyExecution, JourneyMetrics, ABTestResult
)

logger = logging.getLogger(__name__)


class JourneyService:
    """Customer journey orchestration.

    Was written against the legacy sync Session API (db.query(...), bare
    db.commit() with no await) while api/v1/journeys.py injects the app's
    real async AsyncSession -- get_journey_executions/get_ab_test_result/
    get_metrics would raise AttributeError (AsyncSession has no .query()),
    and the three write methods' db.commit() calls were unawaited
    coroutines that never actually executed. This whole feature has been
    non-functional in production independent of the auth issue it was
    originally flagged for. Ported to the real async API throughout.
    """

    @staticmethod
    async def create_journey(business_id: UUID, name: str, nodes: Dict, edges: Dict, db: AsyncSession = None) -> dict:
        if not db:
            raise ValueError("Database session required")

        journey = CustomerJourney(business_id=business_id, name=name, nodes=nodes, edges=edges)
        db.add(journey)
        await db.commit()
        logger.info(f"Journey created: {journey.id}")
        return {"journey_id": str(journey.id), "name": name}

    @staticmethod
    async def create_variant(journey_id: UUID, business_id: UUID, variant_name: str, config: Dict, traffic_allocation: float = 50.0, db: AsyncSession = None) -> dict:
        if not db:
            raise ValueError("Database session required")

        variant = JourneyVariant(journey_id=journey_id, business_id=business_id, variant_name=variant_name, variant_config=config, traffic_allocation=traffic_allocation)
        db.add(variant)
        await db.commit()
        logger.info(f"Variant created: {variant.id}")
        return {"variant_id": str(variant.id), "variant_name": variant_name}

    @staticmethod
    async def enroll_customer(journey_id: UUID, customer_id: UUID, business_id: UUID, variant_id: UUID = None, db: AsyncSession = None) -> dict:
        if not db:
            raise ValueError("Database session required")

        execution = JourneyExecution(journey_id=journey_id, business_id=business_id, customer_id=customer_id, variant_id=variant_id, status="active")
        db.add(execution)
        await db.commit()
        logger.info(f"Customer enrolled: {customer_id} in journey {journey_id}")
        return {"execution_id": str(execution.id), "status": "active"}

    @staticmethod
    async def get_journey_executions(journey_id: UUID, business_id: UUID, limit: int = 50, db: AsyncSession = None) -> List[dict]:
        if not db:
            raise ValueError("Database session required")

        result = await db.execute(
            select(JourneyExecution)
            .where(JourneyExecution.journey_id == journey_id, JourneyExecution.business_id == business_id)
            .order_by(desc(JourneyExecution.started_at))
            .limit(limit)
        )
        executions = result.scalars().all()
        return [{"execution_id": str(e.id), "customer_id": str(e.customer_id), "status": e.status} for e in executions]

    @staticmethod
    async def get_ab_test_result(journey_id: UUID, business_id: UUID, variant_a_id: UUID, variant_b_id: UUID, db: AsyncSession = None) -> dict:
        if not db:
            raise ValueError("Database session required")

        result = await db.execute(
            select(ABTestResult).where(ABTestResult.journey_id == journey_id, ABTestResult.business_id == business_id)
        )
        row = result.scalar_one_or_none()
        if not row:
            return {"message": "No test result found"}

        return {"variant_a_value": row.variant_a_value, "variant_b_value": row.variant_b_value, "winner": row.winner}

    @staticmethod
    async def get_metrics(business_id: UUID, db: AsyncSession = None) -> dict:
        if not db:
            raise ValueError("Database session required")

        result = await db.execute(select(JourneyMetrics).where(JourneyMetrics.business_id == business_id))
        metrics = result.scalar_one_or_none()
        if not metrics:
            return {"message": "No metrics found"}
        return {"total_journeys": metrics.total_journeys, "completion_rate": metrics.completion_rate}
