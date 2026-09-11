"""Celery tasks for Automation Toggles."""

from celery import shared_task
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone, timedelta
import pytz
from dateutil.rrule import rrulestr
import logging

from app.core.config import get_settings
from app.domains.automations.models import ToggleSchedule, AutomationToggle

logger = logging.getLogger(__name__)
settings = get_settings()


@shared_task(bind=True, max_retries=3)
def execute_toggle_schedules(self):
    """Celery task: Execute scheduled toggles that are due."""
    import asyncio

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(_execute_schedules())


async def _execute_schedules():
    """Inner async function to execute schedules."""
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
    )
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        now = datetime.now(timezone.utc)

        # Find all active schedules due for execution
        result = await db.execute(
            select(ToggleSchedule).where(
                (ToggleSchedule.is_active == True) &
                (ToggleSchedule.next_execution_at <= now)
            )
        )
        schedules = result.scalars().all()

        executed = 0
        failed = 0

        for schedule in schedules:
            try:
                # Execute the toggle action
                toggle_result = await db.execute(
                    select(AutomationToggle).where(AutomationToggle.id == schedule.toggle_id)
                )
                toggle = toggle_result.scalar_one_or_none()

                if not toggle:
                    logger.warning(f"Toggle {schedule.toggle_id} not found for schedule {schedule.id}")
                    schedule.failed_count += 1
                    schedule.last_error = "Toggle not found"
                    await db.commit()
                    failed += 1
                    continue

                # Apply the action
                if schedule.action == "enable":
                    toggle.is_enabled = True
                    toggle.enabled_at = now
                elif schedule.action == "disable":
                    toggle.is_enabled = False
                    toggle.disabled_at = now

                # Update schedule tracking
                schedule.last_executed_at = now
                schedule.execution_count += 1
                schedule.last_error = None

                # Calculate next execution time
                if schedule.recurring and schedule.recurrence_rule:
                    try:
                        tz = pytz.timezone(schedule.timezone)
                        now_tz = now.astimezone(tz)

                        # Parse RRULE and get next occurrence
                        rrule = rrulestr(
                            schedule.recurrence_rule,
                            dtstart=schedule.start_time,
                            ignoretz=False,
                        )

                        # Get next occurrence after now
                        next_time = rrule.after(now_tz, inc=False)
                        if next_time:
                            schedule.next_execution_at = next_time.astimezone(timezone.utc)
                        else:
                            # No more occurrences, disable schedule
                            schedule.is_active = False
                            logger.info(f"Schedule {schedule.id} has no more occurrences, disabling")
                    except Exception as e:
                        logger.error(f"Error parsing recurrence rule for schedule {schedule.id}: {e}")
                        schedule.failed_count += 1
                        schedule.last_error = f"Recurrence parsing error: {str(e)}"
                        failed += 1
                        await db.commit()
                        continue
                else:
                    # One-time schedule, disable after execution
                    schedule.is_active = False

                await db.commit()
                executed += 1
                logger.info(f"Executed schedule {schedule.id}: {schedule.action} for toggle {schedule.toggle_id}")

            except Exception as e:
                logger.error(f"Error executing schedule {schedule.id}: {e}")
                schedule.failed_count += 1
                schedule.last_error = str(e)
                await db.commit()
                failed += 1

        await engine.dispose()
        return {
            "executed": executed,
            "failed": failed,
            "total": len(schedules),
        }
