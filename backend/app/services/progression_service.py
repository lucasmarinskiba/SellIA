"""
Lead Progression Service
- Auto-progression on engagement (open, click)
- Status transitions (new → contacted → engaged → qualified)
- No-engagement timeout triggers
- Lead scoring on actions
"""
import logging
from datetime import datetime, timedelta
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Lead, WorkflowExecution, Workflow
from app.core.scheduler import EmailScheduler

logger = logging.getLogger(__name__)

# ============================================================
# LEAD STATUS FLOW
# ============================================================
LEAD_STATUS_FLOW = {
    "new": "contacted",          # After first email sent
    "contacted": "engaged",      # After email open/click
    "engaged": "qualified",      # After response/meeting
    "qualified": "won",          # Closed deal
    # Terminal states: bounced, unsubscribed, lost
}

# ============================================================
# PROGRESSION SERVICE
# ============================================================
class ProgressionService:
    """Manage lead progression through statuses + workflows."""

    def __init__(self, scheduler: EmailScheduler):
        self.scheduler = scheduler

    async def on_email_sent(
        self,
        session: AsyncSession,
        execution_id: int,
        lead_id: int
    ) -> None:
        """Email sent → update lead status to 'contacted'."""
        lead_stmt = select(Lead).where(Lead.id == lead_id)
        result = await session.execute(lead_stmt)
        lead = result.scalar_one_or_none()

        if not lead:
            return

        if lead.status == "new":
            lead.status = "contacted"
            lead.last_contacted = datetime.now()
            await session.commit()
            logger.info(f"📧 Lead {lead_id} status: new → contacted")

    async def on_email_opened(
        self,
        session: AsyncSession,
        execution_id: int,
        lead_id: int
    ) -> None:
        """Email opened → +5 score, potentially engaged."""
        lead_stmt = select(Lead).where(Lead.id == lead_id)
        result = await session.execute(lead_stmt)
        lead = result.scalar_one_or_none()

        if not lead:
            return

        # Update score
        lead.score = min(100, (lead.score or 0) + 5)
        lead.last_contacted = datetime.now()

        # Progress status
        if lead.status in ["new", "contacted"]:
            lead.status = "engaged"
            logger.info(f"📊 Lead {lead_id} status: → engaged (score: {lead.score})")

        # Check if should progress to next workflow step
        await self._progress_workflow_if_ready(session, lead_id, "email_open")

        await session.commit()

    async def on_email_clicked(
        self,
        session: AsyncSession,
        execution_id: int,
        lead_id: int,
        url: str
    ) -> None:
        """Email clicked → +15 score, set engaged."""
        lead_stmt = select(Lead).where(Lead.id == lead_id)
        result = await session.execute(lead_stmt)
        lead = result.scalar_one_or_none()

        if not lead:
            return

        # Update score (strong engagement signal)
        lead.score = min(100, (lead.score or 0) + 15)
        lead.status = "engaged"
        lead.last_contacted = datetime.now()

        await self._progress_workflow_if_ready(session, lead_id, "email_click")

        await session.commit()
        logger.info(f"🔗 Lead {lead_id} clicked. Score: {lead.score}, Status: engaged")

    async def on_email_bounced(
        self,
        session: AsyncSession,
        lead_id: int,
        reason: str
    ) -> None:
        """Email bounced → terminal state."""
        lead_stmt = select(Lead).where(Lead.id == lead_id)
        result = await session.execute(lead_stmt)
        lead = result.scalar_one_or_none()

        if not lead:
            return

        lead.status = "bounced"
        lead.score = 0

        # Stop all pending emails
        await self._halt_workflows(session, lead_id)

        await session.commit()
        logger.warning(f"❌ Lead {lead_id} bounced: {reason}")

    async def on_email_unsubscribed(
        self,
        session: AsyncSession,
        lead_id: int
    ) -> None:
        """Email unsubscribed → terminal state."""
        lead_stmt = select(Lead).where(Lead.id == lead_id)
        result = await session.execute(lead_stmt)
        lead = result.scalar_one_or_none()

        if not lead:
            return

        lead.status = "unsubscribed"

        # Stop all pending emails
        await self._halt_workflows(session, lead_id)

        await session.commit()
        logger.info(f"🚫 Lead {lead_id} unsubscribed")

    async def check_no_engagement_timeout(
        self,
        session: AsyncSession,
        lead_id: int,
        days_threshold: int = 7
    ) -> bool:
        """
        Check if lead has no engagement for X days.
        Returns True if should trigger no-engagement email.
        """
        lead_stmt = select(Lead).where(Lead.id == lead_id)
        result = await session.execute(lead_stmt)
        lead = result.scalar_one_or_none()

        if not lead or not lead.last_contacted:
            return False

        days_since = (datetime.now() - lead.last_contacted).days
        return days_since >= days_threshold

    async def trigger_no_engagement_sequence(
        self,
        session: AsyncSession,
        lead_id: int,
        workflow_id: int,
        scheduler: EmailScheduler
    ) -> dict:
        """Trigger no-engagement email sequence."""
        # Get lead + workflow
        lead_stmt = select(Lead).where(Lead.id == lead_id)
        lead_result = await session.execute(lead_stmt)
        lead = lead_result.scalar_one_or_none()

        if not lead:
            raise ValueError(f"Lead {lead_id} not found")

        # Find NO_ENGAGEMENT step in workflow
        wf_stmt = select(Workflow).where(Workflow.id == workflow_id)
        wf_result = await session.execute(wf_stmt)
        workflow = wf_result.scalar_one_or_none()

        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        steps = workflow.steps or []
        no_eng_step = next(
            (s for s in steps if s.get("trigger_type") == "no_engagement"),
            None
        )

        if not no_eng_step:
            logger.warning(f"No NO_ENGAGEMENT step in workflow {workflow_id}")
            return {"status": "no_step"}

        # Queue no-engagement email
        email_template = no_eng_step.get("email_template", {})
        subject = email_template.get("subject", "Re-engagement")
        body = email_template.get("body", "Hi {lead_name},...")

        # Personalize
        subject = subject.replace("{company}", lead.company or "your company")
        subject = subject.replace("{lead_name}", lead.name or "there")
        body = body.replace("{company}", lead.company or "your company")
        body = body.replace("{lead_name}", lead.name or "there")

        # Create execution + queue
        from app.db.models import WorkflowExecution
        execution = WorkflowExecution(
            workflow_id=workflow_id,
            lead_id=lead_id,
            lead_email=lead.email,
            step_number=no_eng_step.get("step_number", 99),
            email_status="scheduled",
            email_subject=subject,
            email_body=body
        )
        session.add(execution)
        await session.flush()

        task_id = await scheduler.schedule_send_email(
            workflow_execution_id=execution.id,
            lead_email=lead.email,
            subject=subject,
            body=body,
            send_at=None,  # Send immediately
            priority=5
        )

        execution.tracking_id = task_id
        await session.commit()

        logger.info(f"📨 No-engagement email queued for lead {lead_id}")

        return {
            "status": "queued",
            "execution_id": execution.id,
            "tracking_id": task_id
        }

    async def on_status_change(
        self,
        session: AsyncSession,
        lead_id: int,
        old_status: str,
        new_status: str
    ) -> None:
        """Status change → trigger matching workflow step."""
        logger.info(f"📍 Lead {lead_id} status: {old_status} → {new_status}")

        # Find workflows with STATUS_CHANGE trigger
        # (In prod: query DB, for now mock)
        # Workflow step with trigger_status == new_status
        pass

    async def _progress_workflow_if_ready(
        self,
        session: AsyncSession,
        lead_id: int,
        trigger: str
    ) -> None:
        """
        Check if lead is ready for next workflow step.
        Called after email open/click.
        """
        # Get latest execution
        exec_stmt = select(WorkflowExecution).where(
            WorkflowExecution.lead_id == lead_id
        ).order_by(WorkflowExecution.created_at.desc()).limit(1)

        exec_result = await session.execute(exec_stmt)
        execution = exec_result.scalar_one_or_none()

        if not execution:
            return

        # Get workflow
        wf_stmt = select(Workflow).where(Workflow.id == execution.workflow_id)
        wf_result = await session.execute(wf_stmt)
        workflow = wf_result.scalar_one_or_none()

        if not workflow:
            return

        # Check if next step exists
        steps = workflow.steps or []
        next_step_num = execution.step_number + 1
        next_step = next((s for s in steps if s.get("step_number") == next_step_num), None)

        if not next_step:
            logger.info(f"Workflow complete for lead {lead_id} (no more steps)")
            return

        # If next step is immediate/status-change, queue it
        trigger_type = next_step.get("trigger_type")

        if trigger_type == "status_change":
            # Will be triggered by status change elsewhere
            pass
        elif trigger_type == "time_delay":
            # Already queued by workflow service
            pass

        logger.info(f"Lead {lead_id} ready for workflow step {next_step_num}")

    async def _halt_workflows(
        self,
        session: AsyncSession,
        lead_id: int
    ) -> None:
        """Stop all pending emails for lead (bounced/unsubscribed)."""
        exec_stmt = select(WorkflowExecution).where(
            and_(
                WorkflowExecution.lead_id == lead_id,
                WorkflowExecution.email_status.in_(["scheduled", "sent", "delivered"])
            )
        )

        result = await session.execute(exec_stmt)
        executions = result.scalars().all()

        for execution in executions:
            execution.email_status = "halted"
            logger.info(f"⏸️ Halted email for lead {lead_id}")

# ============================================================
# GLOBAL SERVICE
# ============================================================
progression_service: ProgressionService = None

async def init_progression_service(scheduler: EmailScheduler) -> ProgressionService:
    """Initialize service."""
    global progression_service
    progression_service = ProgressionService(scheduler)
    return progression_service

async def get_progression_service() -> ProgressionService:
    """Get service."""
    global progression_service
    if not progression_service:
        raise RuntimeError("Progression service not initialized")
    return progression_service
