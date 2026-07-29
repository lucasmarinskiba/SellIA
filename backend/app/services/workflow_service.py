"""
Workflow Service - Orchestrates leads through email sequences.
- Coordinates between Workflows, Leads, and Email Scheduler
- Handles step progression
- Applies personalization
"""
import logging
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Lead, Workflow, WorkflowExecution
from app.core.scheduler import EmailScheduler
from app.api.v1.workflows import render_email_template

logger = logging.getLogger(__name__)

# ============================================================
# WORKFLOW SERVICE
# ============================================================
class WorkflowService:
    """Orchestrate lead progression through workflows."""

    def __init__(self, scheduler: EmailScheduler):
        self.scheduler = scheduler

    async def enroll_lead(
        self,
        session: AsyncSession,
        workflow_id: int,
        lead_id: int,
        workflow: dict
    ) -> dict:
        """
        Enroll lead in workflow.
        1. Create execution record
        2. Queue first email
        3. Return execution details
        """
        # Get lead details
        lead_stmt = select(Lead).where(Lead.id == lead_id)
        lead_result = await session.execute(lead_stmt)
        lead = lead_result.scalar_one_or_none()

        if not lead:
            raise ValueError(f"Lead {lead_id} not found")

        # Get first step
        steps = workflow.get("steps", [])
        if not steps:
            raise ValueError("Workflow has no steps")

        first_step = next((s for s in steps if s.get("step_number") == 1), None)
        if not first_step:
            raise ValueError("Workflow missing step 1")

        # Prepare email
        email_template = first_step.get("email_template", {})
        lead_data = {
            "name": lead.name,
            "company": lead.company or "your company",
            "industry": lead.industry or "your industry",
            "offer": "SellIA"
        }

        subject, body = render_email_template(
            type('Template', (), email_template),
            lead_data
        )

        # Determine send time
        send_at = None
        trigger_type = first_step.get("trigger_type")

        if trigger_type == "time_delay":
            delay_days = first_step.get("delay_days", 0)
            send_at = datetime.now() + timedelta(days=delay_days)
        elif trigger_type == "no_engagement":
            # NO_ENGAGEMENT trigger: send after delay
            delay_days = first_step.get("delay_days", 7)
            send_at = datetime.now() + timedelta(days=delay_days)

        # Create execution in DB
        execution = WorkflowExecution(
            workflow_id=workflow_id,
            lead_id=lead_id,
            lead_email=lead.email,
            step_number=1,
            email_status="scheduled",
            email_subject=subject,
            email_body=body
        )
        session.add(execution)
        await session.flush()  # Get ID before commit

        # Queue email with scheduler
        task_id = await self.scheduler.schedule_send_email(
            workflow_execution_id=execution.id,
            lead_email=lead.email,
            subject=subject,
            body=body,
            send_at=send_at,
            priority=5
        )

        execution.tracking_id = task_id
        await session.commit()

        logger.info(f"✅ Lead {lead_id} enrolled in workflow {workflow_id} (exec: {execution.id})")

        return {
            "id": execution.id,
            "workflow_id": workflow_id,
            "lead_id": lead_id,
            "lead_email": lead.email,
            "step_number": 1,
            "email_status": "scheduled",
            "tracking_id": task_id,
            "send_at": send_at.isoformat() if send_at else None
        }

    async def progress_to_next_step(
        self,
        session: AsyncSession,
        execution_id: int,
        workflow: dict,
        scheduler: EmailScheduler
    ) -> dict:
        """
        Move execution to next step.
        Called when:
        - Current step delivered successfully
        - Time delay expired
        - Status change triggered
        """
        # Get execution
        exec_stmt = select(WorkflowExecution).where(
            WorkflowExecution.id == execution_id
        )
        exec_result = await session.execute(exec_stmt)
        execution = exec_result.scalar_one_or_none()

        if not execution:
            raise ValueError(f"Execution {execution_id} not found")

        current_step = execution.step_number
        next_step_num = current_step + 1

        # Find next step in workflow
        steps = workflow.get("steps", [])
        next_step = next((s for s in steps if s.get("step_number") == next_step_num), None)

        if not next_step:
            logger.info(f"Workflow complete: no more steps after {current_step}")
            execution.email_status = "completed"
            await session.commit()
            return {"status": "workflow_completed", "execution_id": execution_id}

        # Prepare email for next step
        email_template = next_step.get("email_template", {})
        lead_stmt = select(Lead).where(Lead.id == execution.lead_id)
        lead_result = await session.execute(lead_stmt)
        lead = lead_result.scalar_one_or_none()

        lead_data = {
            "name": lead.name,
            "company": lead.company or "your company",
            "industry": lead.industry or "your industry",
            "offer": "SellIA"
        }

        subject, body = render_email_template(
            type('Template', (), email_template),
            lead_data
        )

        # Determine send time
        send_at = None
        trigger_type = next_step.get("trigger_type")
        delay_days = next_step.get("delay_days", 0)

        if trigger_type in ["time_delay", "no_engagement"]:
            send_at = datetime.now() + timedelta(days=delay_days)

        # Create new execution for next step
        next_execution = WorkflowExecution(
            workflow_id=execution.workflow_id,
            lead_id=execution.lead_id,
            lead_email=execution.lead_email,
            step_number=next_step_num,
            email_status="scheduled",
            email_subject=subject,
            email_body=body
        )
        session.add(next_execution)
        await session.flush()

        # Queue email
        task_id = await self.scheduler.schedule_send_email(
            workflow_execution_id=next_execution.id,
            lead_email=execution.lead_email,
            subject=subject,
            body=body,
            send_at=send_at,
            priority=5
        )

        next_execution.tracking_id = task_id
        await session.commit()

        logger.info(f"⏭️ Execution {execution_id} → step {next_step_num} (new exec: {next_execution.id})")

        return {
            "execution_id": next_execution.id,
            "step_number": next_step_num,
            "tracking_id": task_id,
            "send_at": send_at.isoformat() if send_at else None
        }

# ============================================================
# GLOBAL SERVICE INSTANCE
# ============================================================
service: WorkflowService = None

async def init_workflow_service(scheduler: EmailScheduler) -> WorkflowService:
    """Initialize service."""
    global service
    service = WorkflowService(scheduler)
    return service

async def get_workflow_service() -> WorkflowService:
    """Get service instance."""
    global service
    if not service:
        raise RuntimeError("Workflow service not initialized")
    return service
