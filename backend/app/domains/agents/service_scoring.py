"""Deal Scoring Service

CRUD and analytics for deal scores and alerts.
"""

import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, asc

from app.core.logger import get_logger
from app.domains.agents.models_scoring import DealScore, DealAlert
from app.domains.agents.deal_scorer import DealScorer

logger = get_logger(__name__)


class DealScoringService:
    """Service layer for deal scoring operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ═══════════════════════════════════════════════════════════════════
    # Deal Scores
    # ═══════════════════════════════════════════════════════════════════

    async def get_deal_scores(
        self,
        business_id: uuid.UUID,
        category: Optional[str] = None,
        min_score: Optional[int] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """List deal scores with optional filters."""
        query = select(DealScore).where(DealScore.business_id == business_id)

        if category:
            query = query.where(DealScore.category == category)
        if min_score is not None:
            query = query.where(DealScore.score >= min_score)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Paginated results
        query = query.order_by(desc(DealScore.calculated_at)).offset(offset).limit(limit)
        result = await self.db.execute(query)
        items = result.scalars().all()

        return {
            "items": items,
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    async def get_deal_score_history(
        self,
        conversation_id: uuid.UUID,
    ) -> List[DealScore]:
        """Timeline of scores for a conversation."""
        result = await self.db.execute(
            select(DealScore)
            .where(DealScore.conversation_id == conversation_id)
            .order_by(asc(DealScore.calculated_at))
        )
        return list(result.scalars().all())

    async def calculate_and_save_score(
        self,
        conversation_id: uuid.UUID,
        business_id: Optional[uuid.UUID] = None,
        customer_id: Optional[uuid.UUID] = None,
        precomputed_result: Optional[Any] = None,
    ) -> DealScore:
        """Calculate a new score and persist it."""
        if precomputed_result is not None:
            result = precomputed_result
        else:
            scorer = DealScorer(self.db)
            result = await scorer.calculate_deal_score(conversation_id)

        # Find previous score
        prev_result = await self.db.execute(
            select(DealScore)
            .where(DealScore.conversation_id == conversation_id)
            .order_by(desc(DealScore.calculated_at))
            .limit(1)
        )
        previous = prev_result.scalar_one_or_none()

        previous_score = previous.score if previous else None
        score_change = (
            (result.score - previous_score) if previous_score is not None else None
        )

        deal_score = DealScore(
            conversation_id=conversation_id,
            business_id=business_id,
            customer_id=customer_id,
            score=result.score,
            category=result.category,
            factors=result.factors,
            recommendation=result.recommendation,
            previous_score=previous_score,
            score_change=score_change,
            calculated_at=datetime.now(timezone.utc),
        )
        self.db.add(deal_score)
        await self.db.commit()
        await self.db.refresh(deal_score)

        logger.info(
            f"Deal score calculated for conversation {conversation_id}: "
            f"{result.score} ({result.category})"
        )
        return deal_score

    # ═══════════════════════════════════════════════════════════════════
    # Alerts
    # ═══════════════════════════════════════════════════════════════════

    async def get_alerts(
        self,
        business_id: uuid.UUID,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """List alerts for a business."""
        query = select(DealAlert).where(DealAlert.conversation_id.in_(
            select(DealScore.conversation_id).where(DealScore.business_id == business_id)
        ))

        if unread_only:
            query = query.where(DealAlert.is_read == False)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(desc(DealAlert.created_at)).offset(offset).limit(limit)
        result = await self.db.execute(query)
        items = result.scalars().all()

        return {
            "items": items,
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    async def mark_alert_read(
        self,
        alert_id: uuid.UUID,
    ) -> Optional[DealAlert]:
        """Mark an alert as read."""
        result = await self.db.execute(
            select(DealAlert).where(DealAlert.id == alert_id)
        )
        alert = result.scalar_one_or_none()
        if not alert:
            return None

        alert.is_read = True
        await self.db.commit()
        await self.db.refresh(alert)
        return alert

    async def create_alert(
        self,
        deal_score_id: uuid.UUID,
        conversation_id: uuid.UUID,
        alert_type: str,
        severity: str,
        message: str,
    ) -> DealAlert:
        """Create a new deal alert."""
        alert = DealAlert(
            deal_score_id=deal_score_id,
            conversation_id=conversation_id,
            alert_type=alert_type,
            severity=severity,
            message=message,
        )
        self.db.add(alert)
        await self.db.commit()
        await self.db.refresh(alert)
        logger.info(f"Deal alert created: {alert_type} for conversation {conversation_id}")
        return alert

    # ═══════════════════════════════════════════════════════════════════
    # Pipeline Funnel
    # ═══════════════════════════════════════════════════════════════════

    async def get_pipeline_funnel(
        self,
        business_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """Count deal scores by category (cold/warm/hot/ready)."""
        result = await self.db.execute(
            select(DealScore.category, func.count())
            .where(DealScore.business_id == business_id)
            .group_by(DealScore.category)
        )
        rows = result.all()

        counts = {"cold": 0, "warm": 0, "hot": 0, "ready": 0}
        for category, count in rows:
            if category in counts:
                counts[category] = count

        return {
            "business_id": str(business_id),
            "counts": counts,
            "total": sum(counts.values()),
        }
