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
from app.domains.automations.models import (
    ToggleSchedule,
    AutomationToggle,
    ToggleNotificationRule,
    ToggleNotificationLog,
    ToggleNotificationEventType,
)

logger = logging.getLogger(__name__)
settings = get_settings()


async def send_toggle_notification(
    db: AsyncSession,
    toggle_id: str,
    business_id: str,
    event_type: str,
    toggle_name: str = "Toggle",
):
    """Send notifications for toggle event."""
    from app.core.email import send_email  # Assuming email utility exists

    try:
        # Find matching notification rules
        result = await db.execute(
            select(ToggleNotificationRule).where(
                (ToggleNotificationRule.toggle_id == toggle_id) &
                (ToggleNotificationRule.event_type == event_type) &
                (ToggleNotificationRule.is_active == True)
            )
        )
        rules = result.scalars().all()

        for rule in rules:
            channels_sent = []
            payload = {
                "toggle_id": str(toggle_id),
                "toggle_name": toggle_name,
                "event_type": event_type,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            # Email notification
            if rule.notify_via_email and rule.email_recipients:
                try:
                    subject = f"Toggle Alert: {toggle_name} - {event_type.replace('_', ' ').title()}"
                    body = f"The toggle '{toggle_name}' has {event_type.replace('_', ' ')}."
                    for email in rule.email_recipients:
                        # Queue email task (non-blocking)
                        send_email.delay(to_email=email, subject=subject, body=body)
                    channels_sent.append("email")
                except Exception as e:
                    logger.error(f"Failed to send email notification: {e}")

            # Webhook notification
            if rule.notify_via_webhook and rule.webhook_url:
                try:
                    import httpx
                    async with httpx.AsyncClient(timeout=5) as client:
                        headers = {}
                        if rule.webhook_secret:
                            import hmac
                            import hashlib
                            signature = hmac.new(
                                rule.webhook_secret.encode(),
                                str(payload).encode(),
                                hashlib.sha256,
                            ).hexdigest()
                            headers["X-Signature"] = signature

                        response = await client.post(
                            rule.webhook_url,
                            json=payload,
                            headers=headers,
                        )
                        channels_sent.append("webhook")
                except Exception as e:
                    logger.error(f"Failed to send webhook notification: {e}")

            # Log notification
            log = ToggleNotificationLog(
                business_id=business_id,
                toggle_id=toggle_id,
                rule_id=rule.id,
                event_type=event_type,
                channels_sent=channels_sent,
                email_addresses=rule.email_recipients or [],
                payload=payload,
                status="sent" if channels_sent else "failed",
            )
            db.add(log)
            await db.commit()

    except Exception as e:
        logger.error(f"Error sending toggle notification: {e}")


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

                # Send notifications for scheduled toggle action
                await send_toggle_notification(
                    db=db,
                    toggle_id=str(schedule.toggle_id),
                    business_id=str(schedule.business_id),
                    event_type="schedule_executed",
                    toggle_name=toggle.display_name,
                )

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
