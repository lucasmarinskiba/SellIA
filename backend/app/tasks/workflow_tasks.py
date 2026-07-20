"""Celery Tasks para Workflows, Sequences y Handoffs.

Tareas en background que requieren acceso a la base de datos.
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from asgiref.sync import async_to_sync
from celery import shared_task
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.domains.automations.models import (
    Workflow, WorkflowExecution, WorkflowStatus, EmailSequence, SequenceStep, EmailTemplate,
    SequenceSubscription, SequenceEmailLog,
)
from app.domains.channels.models import Conversation, ChannelConnection, ChannelPlatform
from app.domains.crm.models import Deal, LeadScore
from app.domains.businesses.models import Business


# Helper para correr código async desde sync Celery
def run_async(coro):
    """Run an async coroutine in a sync context."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If already in an async context, use asyncio.run_coroutine_threadsafe
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


@shared_task(bind=True, max_retries=3)
def execute_workflow_task(self, execution_id: str, business_id: str, selected_actions: Optional[List[Dict[str, Any]]] = None):
    """Execute a workflow via Celery task."""
    async def _run():
        async with AsyncSessionLocal() as db:
            from app.domains.automations.engine import WorkflowEngine
            engine = WorkflowEngine(db)
            from uuid import UUID
            await engine.execute_workflow(
                execution_id=UUID(execution_id),
                business_id=UUID(business_id),
                selected_actions=selected_actions,
            )
    try:
        run_async(_run())
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


def _inject_tracking(body: str, tracking_token: str, base_url: str) -> str:
    """Inject open pixel and wrap links with click tracking."""
    if not body:
        return body
    # Inject open tracking pixel at the end
    pixel_url = f"{base_url}/api/v1/track/open/{tracking_token}"
    pixel_html = f'<img src="{pixel_url}" width="1" height="1" alt="" style="display:block;width:1px;height:1px;" />'
    if "</body>" in body:
        body = body.replace("</body>", f"{pixel_html}</body>")
    elif "</html>" in body:
        body = body.replace("</html>", f"{pixel_html}</html>")
    else:
        body = body + pixel_html

    # Wrap links
    import re
    link_pattern = re.compile(r'href=["\'](https?://[^"\']+)["\']', re.IGNORECASE)

    def replace_link(match):
        original_url = match.group(1)
        tracked_url = f"{base_url}/api/v1/track/click/{tracking_token}?url={original_url}"
        return f'href="{tracked_url}"'

    body = link_pattern.sub(replace_link, body)
    return body


@shared_task
def send_sequence_email_task(
    subscription_id: str,
    step_id: str,
):
    """Send a specific step of an email sequence. Supports AI-generated content and tracking."""
    async def _run():
        async with AsyncSessionLocal() as db:
            from uuid import UUID
            import secrets

            # Get subscription
            result = await db.execute(
                select(SequenceSubscription).where(SequenceSubscription.id == subscription_id)
            )
            subscription = result.scalar_one_or_none()
            if not subscription or subscription.status != "active":
                return

            sequence_id = subscription.sequence_id
            conversation_id = subscription.conversation_id
            business_id = subscription.business_id

            # Get sequence step
            result = await db.execute(
                select(SequenceStep).where(SequenceStep.id == step_id)
            )
            step = result.scalar_one_or_none()
            if not step:
                return

            # Get conversation
            result = await db.execute(
                select(Conversation).where(Conversation.id == conversation_id)
            )
            conversation = result.scalar_one_or_none()
            if not conversation or not conversation.lead_email:
                return

            # Get template
            template = None
            if step.template_id:
                result = await db.execute(
                    select(EmailTemplate).where(EmailTemplate.id == step.template_id)
                )
                template = result.scalar_one_or_none()

            # Get business for variable substitution
            result = await db.execute(
                select(Business).where(Business.id == business_id)
            )
            business = result.scalar_one_or_none()

            # Check if AI generation is enabled for this step
            step_extra = step.extra_data or {}
            ai_personality = step_extra.get("ai_personality_slug")

            if ai_personality:
                from app.domains.agents.ai_reply import generate_ai_response
                ai_prompt = step_extra.get("ai_prompt", "")
                template_guide = ""
                if template:
                    template_guide = f"Subject guidance: {template.subject}\nBody guidance: {template.body_text[:500]}"

                custom_prompt = f"""Write an email for this lead.

{template_guide}

{ai_prompt}

The lead's name is: {conversation.lead_name or 'there'}.
Write ONLY the email body text. Be concise and compelling."""

                ai_body = await generate_ai_response(
                    db=db,
                    conversation=conversation,
                    personality_slug=ai_personality,
                    business_id=business_id,
                    custom_prompt=custom_prompt,
                    max_tokens=2000,
                )

                ai_subject = step.subject_override or (template.subject if template else "Mensaje")
                if ai_body:
                    body = ai_body
                    subject = ai_subject
                else:
                    body = step.body_override or (template.body_text if template else "")
                    subject = ai_subject
            else:
                subject = step.subject_override or (template.subject if template else "Mensaje")
                body = step.body_override or (template.body_text if template else "")

            # Variable substitution
            lead_name = conversation.lead_name or ""
            business_name = business.name if business else ""
            subject = subject.replace("{{lead_name}}", lead_name).replace("{{business_name}}", business_name)
            body = body.replace("{{lead_name}}", lead_name).replace("{{business_name}}", business_name)

            # Generate tracking token
            tracking_token = secrets.token_urlsafe(24)

            # Build tracking URL base
            from app.core.config import get_settings
            settings = get_settings()
            base_url = settings.TRACKING_BASE_URL or "http://localhost:8000"

            # Determine if HTML or plain text
            html_body = template.body_html if template and template.body_html else None
            if html_body:
                content_html = _inject_tracking(html_body, tracking_token, base_url)
                # Also inject text body as fallback
                content_text = body
            else:
                content_html = _inject_tracking(f"<html><body><p>{body.replace(chr(10), '<br/>')}</p></body></html>", tracking_token, base_url)
                content_text = body

            # Get SMTP credentials from business email channel
            result = await db.execute(
                select(ChannelConnection).where(
                    ChannelConnection.business_id == business_id,
                    ChannelConnection.platform == ChannelPlatform.EMAIL,
                    ChannelConnection.is_active == True,
                )
            )
            email_channel = result.scalar_one_or_none()
            credentials = email_channel.credentials if email_channel else {}
            channel_settings = email_channel.settings if email_channel else {}

            # Send email
            from app.domains.channels.connectors.email import EmailConnector
            connector = EmailConnector(credentials, channel_settings)

            # Create email log
            log = SequenceEmailLog(
                subscription_id=subscription.id,
                sequence_id=sequence_id,
                step_id=step_id,
                conversation_id=conversation_id,
                business_id=business_id,
                recipient_email=conversation.lead_email,
                subject=subject,
                tracking_token=tracking_token,
                status="pending",
            )
            db.add(log)
            await db.flush()

            try:
                await connector.send_message(
                    conversation.lead_email,
                    content_text,
                    "text",
                    subject=subject,
                )
                log.status = "sent"
                log.sent_at = datetime.now(timezone.utc)

                # Update sequence counters
                result = await db.execute(
                    select(EmailSequence).where(EmailSequence.id == sequence_id)
                )
                seq = result.scalar_one_or_none()
                if seq:
                    seq.sent_count = (seq.sent_count or 0) + 1

                # Update subscription
                subscription.last_sent_at = datetime.now(timezone.utc)
                subscription.current_step_index += 1
                await db.commit()
            except Exception as e:
                log.status = "failed"
                await db.commit()
                from app.core.logger import get_logger
                get_logger(__name__).error(f"Failed to send email: {e}")

    run_async(_run())


@shared_task
def check_pending_workflows():
    """Check for workflow executions that need to be resumed."""
    async def _run():
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(WorkflowExecution).where(
                    WorkflowExecution.status == "running",
                ).order_by(WorkflowExecution.executed_at)
            )
            executions = result.scalars().all()

            now = datetime.now(timezone.utc)
            for execution in executions:
                actions = execution.actions_executed or []
                if not actions:
                    continue

                last_action = actions[-1]
                if last_action.get("status") == "waiting":
                    resume_at_str = last_action.get("resume_at")
                    if resume_at_str:
                        resume_at = datetime.fromisoformat(resume_at_str.replace("Z", "+00:00"))
                        if now >= resume_at:
                            # Resume via Celery task
                            from uuid import UUID
                            wf_result = await db.execute(
                                select(Workflow).where(Workflow.id == execution.workflow_id)
                            )
                            workflow = wf_result.scalar_one_or_none()
                            if workflow:
                                execute_workflow_task.delay(
                                    str(execution.id),
                                    str(workflow.business_id),
                                )

    run_async(_run())


@shared_task
def check_email_sequences():
    """Check for email sequence steps that need to be sent."""
    async def _run():
        async with AsyncSessionLocal() as db:
            now = datetime.now(timezone.utc)

            # Get all active subscriptions
            result = await db.execute(
                select(SequenceSubscription).where(
                    SequenceSubscription.status == "active",
                )
            )
            subscriptions = result.scalars().all()

            for sub in subscriptions:
                # Get sequence steps
                result = await db.execute(
                    select(SequenceStep).where(
                        SequenceStep.sequence_id == sub.sequence_id,
                        SequenceStep.is_active == True,
                    ).order_by(SequenceStep.step_order)
                )
                steps = result.scalars().all()

                if not steps or sub.current_step_index >= len(steps):
                    # Sequence completed
                    sub.status = "completed"
                    await db.commit()
                    continue

                next_step = steps[sub.current_step_index]

                # Calculate due time
                if sub.last_sent_at:
                    delay = timedelta(hours=next_step.delay_hours, minutes=next_step.delay_minutes)
                    due_at = sub.last_sent_at + delay
                else:
                    # First step: send immediately (or after a small delay)
                    due_at = sub.started_at

                if now < due_at:
                    continue

                # Evaluate condition if present
                condition = next_step.condition
                if condition and ":" in condition:
                    key, expected = condition.split(":", 1)
                    if key == "opened_previous":
                        # Check if previous email was opened
                        prev_step_index = sub.current_step_index - 1
                        if prev_step_index >= 0:
                            prev_step = steps[prev_step_index]
                            prev_log_result = await db.execute(
                                select(SequenceEmailLog).where(
                                    SequenceEmailLog.subscription_id == sub.id,
                                    SequenceEmailLog.step_id == prev_step.id,
                                    SequenceEmailLog.opened_at != None,
                                )
                            )
                            was_opened = prev_log_result.scalar_one_or_none() is not None
                            if expected == "yes" and not was_opened:
                                continue
                            if expected == "no" and was_opened:
                                continue
                    elif key == "clicked_previous":
                        prev_step_index = sub.current_step_index - 1
                        if prev_step_index >= 0:
                            prev_step = steps[prev_step_index]
                            prev_log_result = await db.execute(
                                select(SequenceEmailLog).where(
                                    SequenceEmailLog.subscription_id == sub.id,
                                    SequenceEmailLog.step_id == prev_step.id,
                                    SequenceEmailLog.clicked_at != None,
                                )
                            )
                            was_clicked = prev_log_result.scalar_one_or_none() is not None
                            if expected == "yes" and not was_clicked:
                                continue
                            if expected == "no" and was_clicked:
                                continue

                # Schedule send
                send_sequence_email_task.delay(
                    str(sub.id),
                    str(next_step.id),
                )

    run_async(_run())


@shared_task
def check_human_handoffs():
    """Process human handoff queue from Redis."""
    import redis
    from app.core.config import get_settings

    settings = get_settings()
    try:
        r = redis.from_url(settings.REDIS_URL, decode_responses=True)
        # Check queue size
        queue_len = r.llen("human_handoff_queue")
        if queue_len > 0:
            from app.core.logger import get_logger
            get_logger(__name__).info(f"{queue_len} conversations awaiting human")
            # TODO: Send push notifications, emails, or WebSocket events to dashboard
        r.close()
    except Exception as e:
        from app.core.logger import get_logger
        get_logger(__name__).error(f"Redis error: {e}")


@shared_task
def calculate_lead_score_task(conversation_id: str, business_id: str):
    """Recalculate lead score for a conversation."""
    async def _run():
        from uuid import UUID
        from app.domains.crm.scoring import LeadScoringEngine
        async with AsyncSessionLocal() as db:
            engine = LeadScoringEngine(db)
            await engine.calculate_score(
                conversation_id=UUID(conversation_id),
                business_id=UUID(business_id),
            )

    run_async(_run())


@shared_task
def check_deals_stalled():
    """Check for stalled deals and generate alerts."""
    async def _run():
        from app.domains.alerts.engine import AlertEngine
        async with AsyncSessionLocal() as db:
            engine = AlertEngine(db)
            alerts = await engine.check_deal_stalled()
            from app.core.logger import get_logger
            get_logger(__name__).info(f"Generated {len(alerts)} stalled deal alerts")

    run_async(_run())


@shared_task
def check_hot_leads_no_deal():
    """Check for hot leads without deals and generate alerts."""
    async def _run():
        from app.domains.alerts.engine import AlertEngine
        async with AsyncSessionLocal() as db:
            engine = AlertEngine(db)
            alerts = await engine.check_hot_leads_no_deal()
            from app.core.logger import get_logger
            get_logger(__name__).info(f"Generated {len(alerts)} hot-lead-no-deal alerts")

    run_async(_run())


@shared_task
def check_abandoned_carts():
    """Check for abandoned carts and generate alerts."""
    async def _run():
        from app.domains.alerts.engine import AlertEngine
        async with AsyncSessionLocal() as db:
            engine = AlertEngine(db)
            alerts = await engine.check_abandoned_carts()
            from app.core.logger import get_logger
            get_logger(__name__).info(f"Generated {len(alerts)} abandoned cart alerts")

    run_async(_run())


@shared_task
def check_no_reply_conversations():
    """Check for conversations with no reply and generate alerts."""
    async def _run():
        from app.domains.alerts.engine import AlertEngine
        async with AsyncSessionLocal() as db:
            engine = AlertEngine(db)
            alerts = await engine.check_no_reply()
            from app.core.logger import get_logger
            get_logger(__name__).info(f"Generated {len(alerts)} no-reply alerts")

    run_async(_run())



@shared_task
def check_upcoming_appointments():
    """Check for upcoming appointments and send reminders."""
    async def _run():
        from app.domains.services import services as svc_services
        async with AsyncSessionLocal() as db:
            result = await svc_services.check_upcoming_appointments(db)
            from app.core.logger import get_logger
            get_logger(__name__).info(f"Appointment reminders: {result}")

    run_async(_run())


@shared_task
def process_no_show_appointments():
    """Mark past appointments without completion as no-show."""
    async def _run():
        from app.domains.services import services as svc_services
        async with AsyncSessionLocal() as db:
            count = await svc_services.process_no_shows(db)
            from app.core.logger import get_logger
            get_logger(__name__).info(f"No-shows processed: {count}")

    run_async(_run())


@shared_task
def request_pending_confirmations():
    """Request confirmation for pending appointments within 48h."""
    async def _run():
        from app.domains.services import services as svc_services
        async with AsyncSessionLocal() as db:
            count = await svc_services.request_pending_confirmations(db)
            from app.core.logger import get_logger
            get_logger(__name__).info(f"Confirmations requested: {count}")

    run_async(_run())
