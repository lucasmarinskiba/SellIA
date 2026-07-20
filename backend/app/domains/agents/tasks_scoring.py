"""Deal Scoring Celery Tasks

Periodic task to update deal scores and generate alerts.
"""

import asyncio
import uuid
from datetime import datetime, timezone, timedelta
from celery import shared_task
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.logger import get_logger
from app.domains.channels.models import Conversation
from app.domains.agents.service_scoring import DealScoringService
from app.domains.agents.deal_scorer import DealScorer

logger = get_logger(__name__)


def _async_run(coro):
    """Helper to run async coroutine in sync Celery task."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import nest_asyncio
            nest_asyncio.apply()
            return loop.run_until_complete(coro)
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


@shared_task(name="app.domains.agents.tasks_scoring.update_deal_scores_task")
def update_deal_scores_task():
    """Runs every hour to update deal scores for active conversations."""

    async def _run():
        async with AsyncSessionLocal() as db:
            cutoff = datetime.now(timezone.utc) - timedelta(days=7)

            # Find active conversations from last 7 days
            result = await db.execute(
                select(Conversation).where(
                    Conversation.is_active == True,
                    Conversation.last_message_at >= cutoff,
                )
            )
            conversations = result.scalars().all()

            logger.info(f"Updating deal scores for {len(conversations)} active conversations")

            service = DealScoringService(db)
            scorer = DealScorer(db)

            updated = 0
            alerts_created = 0

            for conv in conversations:
                try:
                    # Calculate new score
                    score_result = await scorer.calculate_deal_score(conv.id)

                    # Find previous score
                    from app.domains.agents.models_scoring import DealScore
                    prev_result = await db.execute(
                        select(DealScore)
                        .where(DealScore.conversation_id == conv.id)
                        .order_by(DealScore.calculated_at.desc())
                        .limit(1)
                    )
                    previous = prev_result.scalar_one_or_none()
                    previous_score = previous.score if previous else None

                    # Determine customer_id
                    from app.domains.memory.models import ConversationMemoryChunk
                    chunk_result = await db.execute(
                        select(ConversationMemoryChunk.user_id)
                        .where(ConversationMemoryChunk.conversation_id == conv.id)
                        .limit(1)
                    )
                    chunk_row = chunk_result.first()
                    customer_id = chunk_row[0] if chunk_row else None

                    # Save score (pass precomputed result to avoid double calculation)
                    score = await service.calculate_and_save_score(
                        conversation_id=conv.id,
                        business_id=conv.business_id,
                        customer_id=customer_id,
                        precomputed_result=score_result,
                    )
                    updated += 1

                    # Create alerts based on score changes
                    if previous_score is not None:
                        drop = previous_score - score.score

                        # Score drop > 15 points
                        if drop > 15:
                            await service.create_alert(
                                deal_score_id=score.id,
                                conversation_id=conv.id,
                                alert_type="score_drop",
                                severity="high" if drop > 25 else "medium",
                                message=(
                                    f"Deal score dropped by {drop} points "
                                    f"(from {previous_score} to {score.score}). "
                                    f"Immediate attention recommended."
                                ),
                            )
                            alerts_created += 1

                        # Ready to close (crossed 76 threshold upward)
                        if score.score >= 76 and previous_score < 76:
                            await service.create_alert(
                                deal_score_id=score.id,
                                conversation_id=conv.id,
                                alert_type="ready_to_close",
                                severity="high",
                                message=(
                                    f"Deal is ready to close! Score jumped to {score.score}. "
                                    f"Recommend offering urgency incentive."
                                ),
                            )
                            alerts_created += 1

                        # Deal cooling (crossed 40 threshold downward)
                        if score.score < 40 and previous_score >= 40:
                            await service.create_alert(
                                deal_score_id=score.id,
                                conversation_id=conv.id,
                                alert_type="deal_cooling",
                                severity="medium",
                                message=(
                                    f"Deal is cooling down. Score fell to {score.score}. "
                                    f"Consider re-engagement strategy."
                                ),
                            )
                            alerts_created += 1

                except Exception as exc:
                    logger.warning(f"Failed to score conversation {conv.id}: {exc}")
                    continue

            logger.info(
                f"Deal score update complete: {updated} updated, {alerts_created} alerts created"
            )
            return {"updated": updated, "alerts_created": alerts_created}

    return _async_run(_run())
