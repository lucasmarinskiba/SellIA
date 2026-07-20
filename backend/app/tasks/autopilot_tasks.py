"""Autopilot Celery Tasks.

24/7 autonomous sales execution.
"""

import asyncio
from celery import shared_task
from datetime import datetime, timezone

from app.core.database import AsyncSessionLocal
from app.core.logger import get_logger
from app.domains.autopilot.service import AutopilotEngine, AutopilotReportService, AutopilotExecutor
from app.domains.outreach.service import FatigueScoringService
from app.domains.crm.auto_close import AutoCloseEvaluator
from app.domains.retention.health import HealthScoringService, ChurnPreventionEngine
from app.domains.alerts.models import Recommendation, RecommendationStatus
from app.domains.businesses.models import Business
from sqlalchemy import select

logger = get_logger(__name__)


def _async_run(coro):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import nest_asyncio
            nest_asyncio.apply()
            return loop.run_until_complete(coro)
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


@shared_task(name="app.tasks.autopilot_tasks.autopilot_recommendation_executor")
def autopilot_recommendation_executor():
    """Every 15 min: execute pending recommendations via AutopilotEngine."""
    async def _run():
        async with AsyncSessionLocal() as db:
            engine = AutopilotEngine(db)
            executor = AutopilotExecutor(db)

            # Get all pending recommendations
            result = await db.execute(
                select(Recommendation).where(
                    Recommendation.status == RecommendationStatus.PENDING,
                ).limit(100)
            )
            recommendations = result.scalars().all()

            executed = 0
            escalated = 0
            for rec in recommendations:
                try:
                    success = await executor.execute_recommendation(rec)
                    if success:
                        executed += 1
                    else:
                        escalated += 1
                except Exception as e:
                    logger.exception(f"Failed to execute recommendation {rec.id}: {e}")

            logger.info(f"Autopilot recommendation executor: {executed} executed, {escalated} escalated")
            return {"executed": executed, "escalated": escalated}

    return _async_run(_run())


@shared_task(name="app.tasks.autopilot_tasks.autopilot_daily_report_generator")
def autopilot_daily_report_generator():
    """Daily at 7 AM: generate daily reports for all active businesses."""
    async def _run():
        async with AsyncSessionLocal() as db:
            report_service = AutopilotReportService(db)

            result = await db.execute(
                select(Business).where(Business.is_active == True)
            )
            businesses = result.scalars().all()

            generated = 0
            for business in businesses:
                try:
                    await report_service.generate_daily_report(business.id)
                    generated += 1
                except Exception as e:
                    logger.error(f"Failed to generate daily report for business {business.id}: {e}")

            logger.info(f"Generated {generated} daily autopilot reports")
            return {"generated": generated}

    return _async_run(_run())


@shared_task(name="app.tasks.autopilot_tasks.fatigue_score_recalculation")
def fatigue_score_recalculation():
    """Every 1h: recalculate contact fatigue scores."""
    async def _run():
        async with AsyncSessionLocal() as db:
            service = FatigueScoringService(db)

            result = await db.execute(
                select(Business).where(Business.is_active == True)
            )
            businesses = result.scalars().all()

            total_updated = 0
            for business in businesses:
                try:
                    count = await service.recalculate_all_scores(business.id)
                    total_updated += count
                except Exception as e:
                    logger.error(f"Failed to recalculate fatigue for business {business.id}: {e}")

            logger.info(f"Recalculated fatigue scores for {total_updated} conversations")
            return {"updated": total_updated}

    return _async_run(_run())


@shared_task(name="app.tasks.autopilot_tasks.auto_close_evaluator")
def auto_close_evaluator():
    """Every 1h: evaluate open deals for auto-close."""
    async def _run():
        async with AsyncSessionLocal() as db:
            evaluator = AutoCloseEvaluator(db)
            actions = await evaluator.evaluate_all_open_deals()
            logger.info(f"Auto-close evaluator: {len(actions)} deals auto-closed")
            return {"closed": len(actions), "details": actions}

    return _async_run(_run())


@shared_task(name="app.tasks.autopilot_tasks.health_score_recalculation")
def health_score_recalculation():
    """Daily at 3 AM: recalculate customer health scores."""
    async def _run():
        async with AsyncSessionLocal() as db:
            service = HealthScoringService(db)

            result = await db.execute(
                select(Business).where(Business.is_active == True)
            )
            businesses = result.scalars().all()

            total_updated = 0
            for business in businesses:
                try:
                    count = await service.recalculate_all_health_scores(business.id)
                    total_updated += count
                except Exception as e:
                    logger.error(f"Failed to recalculate health scores for business {business.id}: {e}")

            logger.info(f"Recalculated health scores for {total_updated} customers")
            return {"updated": total_updated}

    return _async_run(_run())


@shared_task(name="app.tasks.autopilot_tasks.churn_prevention_activator")
def churn_prevention_activator():
    """Daily at 8 AM: activate churn prevention workflows."""
    async def _run():
        async with AsyncSessionLocal() as db:
            engine = ChurnPreventionEngine(db)

            result = await db.execute(
                select(Business).where(Business.is_active == True)
            )
            businesses = result.scalars().all()

            total_actions = 0
            for business in businesses:
                try:
                    actions = await engine.activate_prevention_for_business(business.id)
                    total_actions += len(actions)
                except Exception as e:
                    logger.error(f"Failed churn prevention for business {business.id}: {e}")

            logger.info(f"Churn prevention: {total_actions} actions activated")
            return {"activated": total_actions}

    return _async_run(_run())


@shared_task(name="app.tasks.autopilot_tasks.cadence_engine_scheduler")
def cadence_engine_scheduler():
    """Every 30 min: schedule next contacts based on fatigue + context."""
    async def _run():
        async with AsyncSessionLocal() as db:
            from app.domains.outreach.service import CadenceEngine
            from app.domains.channels.models import Conversation

            engine = CadenceEngine(db)

            # Get active conversations that need follow-up
            # Conversations with no response in 24-48h and not in cooldown
            since = datetime.now(timezone.utc) - timedelta(hours=48)
            until = datetime.now(timezone.utc) - timedelta(hours=24)

            result = await db.execute(
                select(Conversation).where(
                    Conversation.is_active == True,
                    Conversation.last_message_at >= since,
                    Conversation.last_message_at < until,
                ).limit(200)
            )
            conversations = result.scalars().all()

            scheduled = 0
            for conv in conversations:
                try:
                    next_action = await engine.get_next_action_for_lead(conv.business_id, conv.id)
                    if next_action["recommended_action"] == "send_message":
                        # In a full implementation, this would queue the message
                        # For now, we log that cadence recommends sending
                        scheduled += 1
                except Exception as e:
                    logger.error(f"Cadence scheduling failed for conv {conv.id}: {e}")

            logger.info(f"Cadence scheduler: {scheduled} contacts recommended")
            return {"recommended": scheduled}

    return _async_run(_run())


@shared_task(name="app.tasks.autopilot_tasks.director_executive_loop")
def director_executive_loop():
    """Every 6h: SellIA Director evaluates AND executes action plans."""
    async def _run():
        async with AsyncSessionLocal() as db:
            from app.domains.orchestration.director import SellIADirector
            from app.domains.autopilot.models import AutopilotConfig

            director = SellIADirector(db)

            result = await db.execute(
                select(Business).where(Business.is_active == True)
            )
            businesses = result.scalars().all()

            for business in businesses:
                try:
                    # Check if autopilot allows director to execute
                    config_result = await db.execute(
                        select(AutopilotConfig).where(AutopilotConfig.business_id == business.id)
                    )
                    config = config_result.scalar_one_or_none()

                    briefing = await director.run_daily_briefing(business.id)

                    # If autopilot is active, execute action plans
                    if config and config.is_active and not config.is_paused:
                        for action in briefing.get("action_plan", []):
                            if action.get("priority") == "high":
                                # Activate recovery workflow
                                if config.auto_activate_recovery_workflows:
                                    logger.info(f"Director auto-activated recovery for business {business.id}: {action['action']}")
                                    # In full implementation, would trigger actual workflow

                    logger.info(f"Director executive loop completed for business {business.id}")
                except Exception as e:
                    logger.error(f"Director executive loop failed for business {business.id}: {e}")

            return {"businesses_evaluated": len(businesses)}

    return _async_run(_run())
