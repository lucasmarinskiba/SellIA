"""
Celery tasks for System Intelligence Engine.

Automated analysis, improvement generation, and rollout.
"""

from datetime import datetime, timezone, timedelta

from celery import shared_task

from app.core.logger import get_logger

logger = get_logger(__name__)


@shared_task
async def hourly_system_analysis():
    """Genera System Health Report cada hora."""
    from app.core.database import AsyncSessionLocal
    from app.core.intelligence.system_analyzer import generate_health_report

    async with AsyncSessionLocal() as db:
        report = await generate_health_report(db)
        logger.info(f"Hourly system analysis: {report.unresolved_tickets} unresolved tickets, {len(report.top_feedback_themes)} feedback themes")
        return report.to_dict()


@shared_task
async def daily_improvement_generation():
    """Genera propuestas de mejora diariamente."""
    from app.core.database import AsyncSessionLocal
    from app.core.intelligence.system_analyzer import generate_health_report
    from app.core.intelligence.improvement_generator import generate_improvements
    from app.domains.businesses.models import Business
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        # Get first business as context
        result = await db.execute(select(Business).limit(1))
        business = result.scalar_one_or_none()
        business_id = business.id if business else uuid.UUID(int=0)

        report = await generate_health_report(db)
        improvements = await generate_improvements(db, report, business_id)

        logger.info(f"Generated {len(improvements)} daily improvements")
        return {"improvements_created": len(improvements)}


@shared_task
async def weekly_feedback_synthesis():
    """Síntesis semanal de todo el feedback para detectar patrones."""
    from app.core.database import AsyncSessionLocal
    from app.domains.feedback.service import FeedbackService
    from app.domains.feedback.models import FeedbackType

    async with AsyncSessionLocal() as db:
        svc = FeedbackService(db)

        # Count by type
        bugs, _ = await svc.list_feedback(type=FeedbackType.BUG)
        ideas, _ = await svc.list_feedback(type=FeedbackType.IDEA)
        complaints, _ = await svc.list_feedback(type=FeedbackType.COMPLAINT)

        logger.info(f"Weekly synthesis: {len(bugs)} bugs, {len(ideas)} ideas, {len(complaints)} complaints")
        return {
            "bugs": len(bugs),
            "ideas": len(ideas),
            "complaints": len(complaints),
        }


@shared_task
async def apply_approved_improvements():
    """Aplica mejoras aprobadas creando feature flags."""
    from app.core.database import AsyncSessionLocal
    from app.domains.feedback.models import SystemImprovement
    from app.core.intelligence.improvement_generator import create_feature_flag_for_improvement
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(SystemImprovement).where(SystemImprovement.status == "approved")
        )
        improvements = result.scalars().all()

        for imp in improvements:
            try:
                await create_feature_flag_for_improvement(db, imp)
            except Exception as e:
                logger.error(f"Failed to create feature flag for {imp.id}: {e}")

        logger.info(f"Applied {len(improvements)} approved improvements")
        return {"applied": len(improvements)}


@shared_task
async def rollout_progressive():
    """Incrementa gradualmente el rollout de features en progreso."""
    from app.core.database import AsyncSessionLocal
    from app.domains.feedback.models import FeatureFlag
    from app.core.intelligence.feature_flags import increment_rollout
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(FeatureFlag).where(
                FeatureFlag.is_active == True,
                FeatureFlag.rollout_percentage < 100,
            )
        )
        flags = result.scalars().all()

        for flag in flags:
            try:
                await increment_rollout(db, flag.name, increment=10)
            except Exception as e:
                logger.error(f"Failed to increment rollout for {flag.name}: {e}")

        logger.info(f"Progressive rollout updated for {len(flags)} features")
        return {"flags_updated": len(flags)}


@shared_task
async def notify_users_of_new_features():
    """Notifica a usuarios cuando una feature que solicitaron se despliega."""
    from app.core.database import AsyncSessionLocal
    from app.domains.feedback.models import UserFeedback, SystemImprovement
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        # Find shipped improvements linked to feedback
        result = await db.execute(
            select(SystemImprovement).where(
                SystemImprovement.status == "deployed",
                SystemImprovement.deployed_at >= datetime.now(timezone.utc) - timedelta(days=1),
            )
        )
        improvements = result.scalars().all()

        for imp in improvements:
            if imp.source_feedback_ids:
                for fb_id in imp.source_feedback_ids:
                    # TODO: Send email/push notification to the user who submitted this feedback
                    logger.info(f"Would notify user about shipped improvement {imp.id} from feedback {fb_id}")

        return {"notifications_sent": len(improvements)}
