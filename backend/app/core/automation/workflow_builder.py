"""
Workflow Builder — Define complex automation workflows.

Permite definir: "si A entonces B else C"

Example workflows:
1. Daily Sales Workflow
   - 9am: post 5 products
   - Every 30min: respond to inquiries
   - 6pm: send follow-up emails to hot leads
   - 11pm: generate daily report

2. Lead Nurturing Workflow
   - Day 0: capture lead
   - Day 1: send welcome email
   - Day 3: send product demo video
   - Day 5: send discount offer
   - Day 7: final urgency email
   - If no response → mark inactive

3. Inventory Sync Workflow
   - Hourly: check inventory
   - If stock low: reduce listings, increase price
   - If stock high: increase listings, discount

4. Customer Support Workflow
   - Real-time: respond to inquiries
   - If resolution unclear: escalate to human
   - If resolved: send satisfaction survey
   - Follow-up: check satisfaction → upsell if happy
"""

import logging
from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class WorkflowTrigger(Enum):
    """Triggers para iniciar workflows."""
    SCHEDULE = "schedule"  # Cron-based
    EVENT = "event"  # Event-driven
    MANUAL = "manual"  # Manual trigger


class WorkflowStatus(Enum):
    """Estado del workflow."""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class WorkflowStep:
    """Un paso en el workflow."""
    id: str
    name: str
    action: str  # Job type (post_product, send_email, etc)
    payload: Dict[str, Any]
    conditions: List[Dict[str, Any]] = field(default_factory=list)
    on_success: Optional[str] = None  # Siguiente step ID
    on_failure: Optional[str] = None  # Step a ejecutar si falla
    timeout_seconds: int = 300
    max_retries: int = 3


@dataclass
class WorkflowCondition:
    """Condición para ejecución condicional."""
    field: str
    operator: str  # eq, gt, lt, in, contains
    value: Any
    next_step: str  # Step ID a ejecutar si true


@dataclass
class Workflow:
    """Define un workflow completo."""
    id: str
    name: str
    description: str
    trigger: WorkflowTrigger
    schedule: Optional[str] = None  # Cron if SCHEDULE trigger
    steps: List[WorkflowStep] = field(default_factory=list)
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_run: Optional[datetime] = None
    execution_count: int = 0
    failure_count: int = 0


class WorkflowBuilder:
    """Construye workflows complejos."""

    def __init__(self):
        self.workflows: Dict[str, Workflow] = {}
        self.step_handlers: Dict[str, Callable] = {}

    def create_workflow(
        self,
        name: str,
        description: str,
        trigger: WorkflowTrigger,
        schedule: Optional[str] = None,
    ) -> Workflow:
        """Crea nuevo workflow."""
        workflow = Workflow(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            trigger=trigger,
            schedule=schedule,
        )
        self.workflows[workflow.id] = workflow
        logger.info(f"Workflow created: {name} (id: {workflow.id})")
        return workflow

    def add_step(
        self,
        workflow_id: str,
        name: str,
        action: str,
        payload: Dict[str, Any],
        timeout_seconds: int = 300,
        max_retries: int = 3,
    ) -> str:
        """Agrega step al workflow."""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        step = WorkflowStep(
            id=str(uuid.uuid4()),
            name=name,
            action=action,
            payload=payload,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
        )

        # Link to previous step
        if workflow.steps:
            workflow.steps[-1].on_success = step.id

        workflow.steps.append(step)
        logger.debug(f"Step added to workflow: {name}")
        return step.id

    def add_condition(
        self,
        workflow_id: str,
        field: str,
        operator: str,
        value: Any,
        next_step_id: str,
    ) -> None:
        """Agrega condición al último step."""
        workflow = self.workflows.get(workflow_id)
        if not workflow or not workflow.steps:
            raise ValueError("Invalid workflow or no steps")

        last_step = workflow.steps[-1]
        condition = WorkflowCondition(
            field=field,
            operator=operator,
            value=value,
            next_step=next_step_id,
        )
        last_step.conditions.append(condition)
        logger.debug(f"Condition added to step: {field} {operator} {value}")

    def add_escalation(
        self,
        workflow_id: str,
        trigger_condition: str,
        escalation_message: str,
    ) -> None:
        """Agrega escalación automática."""
        workflow = self.workflows.get(workflow_id)
        if not workflow or not workflow.steps:
            raise ValueError("Invalid workflow")

        last_step = workflow.steps[-1]
        # Add as on_failure handler with escalation payload
        last_step.on_failure = "escalate"
        logger.debug(f"Escalation added: {escalation_message}")

    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Obtiene workflow."""
        return self.workflows.get(workflow_id)

    def list_workflows(self) -> List[Workflow]:
        """Lista todos workflows."""
        return list(self.workflows.values())

    def enable_workflow(self, workflow_id: str) -> bool:
        """Habilita workflow."""
        workflow = self.workflows.get(workflow_id)
        if workflow:
            workflow.enabled = True
            logger.info(f"Workflow enabled: {workflow.name}")
            return True
        return False

    def disable_workflow(self, workflow_id: str) -> bool:
        """Deshabilita workflow."""
        workflow = self.workflows.get(workflow_id)
        if workflow:
            workflow.enabled = False
            logger.info(f"Workflow disabled: {workflow.name}")
            return True
        return False


class WorkflowExecutor:
    """Ejecuta workflows."""

    def __init__(self, automation_engine):
        self.automation_engine = automation_engine
        self.execution_history: Dict[str, List[Dict[str, Any]]] = {}

    async def execute_workflow(
        self,
        workflow: Workflow,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Ejecuta workflow desde el primer step.

        Args:
            workflow: Workflow a ejecutar
            context: Datos iniciales para el workflow

        Returns:
            Resultado de ejecución
        """
        execution_id = str(uuid.uuid4())
        context = context or {}

        logger.info(f"Executing workflow: {workflow.name} (exec: {execution_id})")

        workflow.execution_count += 1
        workflow.last_run = datetime.utcnow()

        if workflow.id not in self.execution_history:
            self.execution_history[workflow.id] = []

        execution_result = {
            "execution_id": execution_id,
            "workflow_id": workflow.id,
            "status": "running",
            "started_at": datetime.utcnow().isoformat(),
            "steps_executed": [],
        }

        try:
            # Execute first step
            if workflow.steps:
                result = await self._execute_step(
                    workflow,
                    workflow.steps[0],
                    context,
                    execution_result,
                )
                execution_result["status"] = "success"
                execution_result["result"] = result
            else:
                raise ValueError("Workflow has no steps")

        except Exception as e:
            logger.error(f"Workflow execution failed: {str(e)}")
            execution_result["status"] = "failed"
            execution_result["error"] = str(e)
            workflow.failure_count += 1

        execution_result["completed_at"] = datetime.utcnow().isoformat()
        self.execution_history[workflow.id].append(execution_result)

        return execution_result

    async def _execute_step(
        self,
        workflow: Workflow,
        step: WorkflowStep,
        context: Dict[str, Any],
        execution_result: Dict[str, Any],
    ) -> Any:
        """Ejecuta un step del workflow."""
        logger.debug(f"Executing step: {step.name}")

        # Merge step payload with context
        payload = {**context, **step.payload}

        # Create job
        from automation_engine import Job, Priority, JobStatus

        job = Job(
            id=str(uuid.uuid4()),
            job_type=self._string_to_job_type(step.action),
            priority=Priority.HIGH,
            payload=payload,
        )

        # Enqueue and wait for execution
        await self.automation_engine.job_queue.enqueue(job)

        # Track step
        execution_result["steps_executed"].append({
            "step_id": step.id,
            "step_name": step.name,
            "job_id": job.id,
            "executed_at": datetime.utcnow().isoformat(),
        })

        # TODO: Wait for job completion (implement future/promise pattern)

        # Evaluate conditions
        next_step_id = step.on_success
        for condition in step.conditions:
            if self._evaluate_condition(condition, context):
                next_step_id = condition.next_step
                break

        # Execute next step if any
        if next_step_id:
            next_step = self._find_step_by_id(workflow, next_step_id)
            if next_step:
                return await self._execute_step(
                    workflow,
                    next_step,
                    context,
                    execution_result,
                )

        return {"status": "completed"}

    @staticmethod
    def _string_to_job_type(action: str):
        """Convierte string a JobType enum."""
        from automation_engine import JobType

        action_upper = action.upper()
        for job_type in JobType:
            if job_type.value.replace("_", "").upper() == action_upper.replace("_", ""):
                return job_type
        return JobType.POST_PRODUCT  # Default

    @staticmethod
    def _evaluate_condition(
        condition: WorkflowCondition,
        context: Dict[str, Any],
    ) -> bool:
        """Evalúa condición."""
        value = context.get(condition.field)
        if value is None:
            return False

        if condition.operator == "eq":
            return value == condition.value
        elif condition.operator == "gt":
            return value > condition.value
        elif condition.operator == "lt":
            return value < condition.value
        elif condition.operator == "in":
            return value in condition.value
        elif condition.operator == "contains":
            return condition.value in str(value)

        return False

    @staticmethod
    def _find_step_by_id(workflow: Workflow, step_id: str) -> Optional[WorkflowStep]:
        """Busca step por ID."""
        for step in workflow.steps:
            if step.id == step_id:
                return step
        return None


# Built-in workflow templates
def create_daily_sales_workflow(builder: WorkflowBuilder) -> Workflow:
    """Workflow: Daily Sales Automation."""
    workflow = builder.create_workflow(
        name="Daily Sales Workflow",
        description="Posts products, responds to inquiries, sends emails",
        trigger=WorkflowTrigger.SCHEDULE,
        schedule="0 9 * * *",  # 9am
    )

    builder.add_step(
        workflow.id,
        "Post morning products",
        "post_product",
        {"count": 5, "time_of_day": "morning"},
    )

    builder.add_step(
        workflow.id,
        "Respond to inquiries",
        "respond_inquiry",
        {"batch": True},
    )

    builder.add_step(
        workflow.id,
        "Send follow-up emails",
        "send_email",
        {"template": "hot_leads_followup"},
    )

    builder.add_step(
        workflow.id,
        "Generate daily report",
        "generate_report",
        {"report_type": "daily_sales"},
    )

    return workflow


def create_lead_nurturing_workflow(builder: WorkflowBuilder) -> Workflow:
    """Workflow: Lead Nurturing Campaign."""
    workflow = builder.create_workflow(
        name="Lead Nurturing Workflow",
        description="Multi-day email campaign to convert leads",
        trigger=WorkflowTrigger.EVENT,
    )

    # Day 1
    builder.add_step(
        workflow.id,
        "Send welcome email",
        "send_email",
        {"template": "welcome", "delay_hours": 0},
    )

    # Day 3
    builder.add_step(
        workflow.id,
        "Send product demo",
        "send_email",
        {"template": "product_demo", "delay_hours": 72},
    )

    # Day 5
    builder.add_step(
        workflow.id,
        "Send discount offer",
        "send_email",
        {"template": "discount_offer", "delay_hours": 120},
    )

    # Day 7 - Urgency
    builder.add_step(
        workflow.id,
        "Send final email",
        "send_email",
        {"template": "urgency", "delay_hours": 168},
    )

    return workflow
