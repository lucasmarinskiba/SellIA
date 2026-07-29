"""
Task Processor - Executes email scheduler queue.
Runs in background thread/worker process.
"""
import logging
import asyncio
from datetime import datetime
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.scheduler import EmailScheduler, TaskType, TaskStatus
from app.core.email_sender import get_email_sender
from app.db import AsyncSessionLocal
from app.db.models import WorkflowExecution, Lead, EmailLog

logger = logging.getLogger(__name__)

# ============================================================
# TASK PROCESSOR
# ============================================================
class TaskProcessor:
    """Process tasks from scheduler queue."""

    def __init__(self, scheduler: EmailScheduler, batch_size: int = 10):
        self.scheduler = scheduler
        self.batch_size = batch_size
        self.sender = get_email_sender()
        self.running = False

    async def start(self) -> None:
        """Start processing tasks (runs forever until stopped)."""
        self.running = True
        logger.info("🚀 Task processor started")

        while self.running:
            try:
                # Move delayed tasks to queue if ready
                await self.scheduler.move_delayed_to_queue()

                # Process batch of tasks
                for _ in range(self.batch_size):
                    task = await self.scheduler.pop_task()
                    if not task:
                        break

                    await self._process_task(task)

                # Sleep to avoid tight loop
                await asyncio.sleep(5)

            except Exception as e:
                logger.error(f"Processor error: {e}")
                await asyncio.sleep(10)

    async def stop(self) -> None:
        """Stop processor."""
        self.running = False
        logger.info("🛑 Task processor stopped")

    async def _process_task(self, task: dict) -> None:
        """Process single task."""
        try:
            task_type = task.get("type")

            if task_type == TaskType.SEND_WORKFLOW_EMAIL:
                await self._send_workflow_email(task)

            elif task_type == TaskType.SEND_BATCH_EMAILS:
                await self._send_batch_emails(task)

            elif task_type == TaskType.UPDATE_LEAD_SCORE:
                await self._update_lead_score(task)

            elif task_type == TaskType.PROGRESS_WORKFLOW:
                await self._progress_workflow(task)

            else:
                logger.warning(f"Unknown task type: {task_type}")

            await self.scheduler.mark_completed(task)

        except Exception as e:
            logger.error(f"Task processing error: {e}")
            await self.scheduler.mark_failed(task, str(e), retry=True)

    async def _send_workflow_email(self, task: dict) -> None:
        """Send single workflow email."""
        workflow_execution_id = task.get("workflow_execution_id")
        lead_email = task.get("lead_email")
        subject = task.get("subject")
        body = task.get("body")

        try:
            # Send via email sender
            result = await self.sender.send_email(
                to=lead_email,
                subject=subject,
                body=body,
                tracking_id=f"wf_{workflow_execution_id}"
            )

            # Update DB
            async with AsyncSessionLocal() as session:
                # Update execution status
                stmt = select(WorkflowExecution).where(
                    WorkflowExecution.id == workflow_execution_id
                )
                exec_result = await session.execute(stmt)
                execution = exec_result.scalar_one_or_none()

                if execution:
                    execution.email_status = "sent"
                    execution.sent_at = datetime.now()

                # Log email
                email_log = EmailLog(
                    tracking_id=f"wf_{workflow_execution_id}",
                    workflow_execution_id=workflow_execution_id,
                    lead_email=lead_email,
                    subject=subject,
                    provider=result.get("provider"),
                    status=result.get("status")
                )
                session.add(email_log)

                await session.commit()

            logger.info(f"📨 Email sent: {lead_email} (ID: {workflow_execution_id})")

        except Exception as e:
            logger.error(f"Send email failed: {e}")
            raise

    async def _send_batch_emails(self, task: dict) -> None:
        """Send batch of emails."""
        workflow_id = task.get("workflow_id")
        leads = task.get("leads", [])

        logger.info(f"📨 Sending batch: {len(leads)} emails for workflow {workflow_id}")

        for lead_data in leads:
            try:
                lead_id = lead_data.get("id")
                lead_email = lead_data.get("email")
                subject = lead_data.get("subject")
                body = lead_data.get("body")

                # Send
                await self.sender.send_email(
                    to=lead_email,
                    subject=subject,
                    body=body,
                    tracking_id=f"batch_{workflow_id}_{lead_id}"
                )

                logger.info(f"✅ Batch email sent: {lead_email}")

            except Exception as e:
                logger.error(f"Batch send failed for {lead_data.get('email')}: {e}")
                continue

    async def _update_lead_score(self, task: dict) -> None:
        """Update lead score (triggered by engagement)."""
        lead_id = task.get("lead_id")
        score_delta = task.get("score_delta", 0)
        reason = task.get("reason", "engagement")

        try:
            async with AsyncSessionLocal() as session:
                stmt = select(Lead).where(Lead.id == lead_id)
                result = await session.execute(stmt)
                lead = result.scalar_one_or_none()

                if lead:
                    lead.score = min(100, max(0, (lead.score or 0) + score_delta))
                    lead.updated_at = datetime.now()
                    await session.commit()

                    logger.info(f"📊 Lead {lead_id} score updated: {score_delta} ({reason})")

        except Exception as e:
            logger.error(f"Score update failed: {e}")
            raise

    async def _progress_workflow(self, task: dict) -> None:
        """Progress lead to next workflow step."""
        workflow_execution_id = task.get("workflow_execution_id")
        next_step = task.get("next_step")
        delay_minutes = task.get("delay_minutes", 0)

        try:
            async with AsyncSessionLocal() as session:
                stmt = select(WorkflowExecution).where(
                    WorkflowExecution.id == workflow_execution_id
                )
                result = await session.execute(stmt)
                execution = result.scalar_one_or_none()

                if execution:
                    execution.step_number = next_step
                    execution.email_status = "scheduled"
                    await session.commit()

                    logger.info(f"⏭️ Workflow progressed: {workflow_execution_id} → step {next_step}")

        except Exception as e:
            logger.error(f"Workflow progress failed: {e}")
            raise

# ============================================================
# GLOBAL PROCESSOR INSTANCE
# ============================================================
processor: TaskProcessor = None

async def init_processor(scheduler: EmailScheduler) -> TaskProcessor:
    """Initialize global processor."""
    global processor
    processor = TaskProcessor(scheduler)
    return processor

async def start_processor() -> None:
    """Start processor (call from app startup)."""
    global processor
    if processor:
        await processor.start()

async def stop_processor() -> None:
    """Stop processor (call from app shutdown)."""
    global processor
    if processor:
        await processor.stop()

async def get_processor_stats() -> dict:
    """Get processor queue stats."""
    global processor
    if not processor:
        return {"error": "processor not initialized"}

    return await processor.scheduler.get_queue_stats()
