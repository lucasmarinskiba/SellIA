from dataclasses import dataclass, asdict
from typing import Optional, Any, Callable
from enum import Enum
import uuid


class ActionType(str, Enum):
    SEND_EMAIL = "send_email"
    SEND_SMS = "send_sms"
    CREATE_TASK = "create_task"
    UPDATE_FIELD = "update_field"
    CALL_WEBHOOK = "call_webhook"
    WAIT = "wait"
    CONDITIONAL = "conditional"
    LOOP = "loop"


class TriggerType(str, Enum):
    DEAL_CREATED = "deal_created"
    DEAL_STAGE_CHANGED = "deal_stage_changed"
    COMMENT_ADDED = "comment_added"
    APPROVAL_REQUESTED = "approval_requested"
    MANUAL = "manual"
    SCHEDULED = "scheduled"


@dataclass
class WorkflowStep:
    id: str
    action_type: ActionType
    config: dict
    description: Optional[str] = None
    next_step_id: Optional[str] = None
    error_step_id: Optional[str] = None


@dataclass
class WorkflowTrigger:
    type: TriggerType
    conditions: dict


@dataclass
class Workflow:
    id: str
    user_id: str
    name: str
    description: Optional[str]
    trigger: WorkflowTrigger
    steps: list[WorkflowStep]
    is_active: bool
    created_at: str


class WorkflowEngine:
    """Execute automated workflows with conditional logic."""

    def __init__(self):
        self.workflows: dict[str, Workflow] = {}
        self.executions: dict[str, dict] = {}
        self.actions: dict[str, Callable] = {
            ActionType.SEND_EMAIL: self._send_email,
            ActionType.SEND_SMS: self._send_sms,
            ActionType.CREATE_TASK: self._create_task,
            ActionType.UPDATE_FIELD: self._update_field,
            ActionType.CALL_WEBHOOK: self._call_webhook,
            ActionType.WAIT: self._wait,
            ActionType.CONDITIONAL: self._conditional,
            ActionType.LOOP: self._loop,
        }

    def create_workflow(
        self,
        user_id: str,
        name: str,
        trigger: WorkflowTrigger,
        steps: list[WorkflowStep],
        description: Optional[str] = None,
    ) -> Workflow:
        """Create automation workflow."""
        workflow_id = str(uuid.uuid4())
        workflow = Workflow(
            id=workflow_id,
            user_id=user_id,
            name=name,
            description=description,
            trigger=trigger,
            steps=steps,
            is_active=True,
            created_at=str(uuid.uuid4()),
        )
        self.workflows[workflow_id] = workflow
        return workflow

    def execute_workflow(self, workflow_id: str, context: dict) -> dict:
        """Execute workflow with given context."""
        if workflow_id not in self.workflows:
            return {'success': False, 'error': 'Workflow not found'}

        workflow = self.workflows[workflow_id]
        execution_id = str(uuid.uuid4())

        try:
            results = []
            current_step = workflow.steps[0] if workflow.steps else None

            while current_step:
                action_func = self.actions.get(current_step.action_type)
                if not action_func:
                    results.append({'step_id': current_step.id, 'status': 'skipped'})
                    break

                result = action_func(current_step, context)
                results.append({'step_id': current_step.id, 'status': result.get('status')})

                if not result.get('success') and current_step.error_step_id:
                    current_step = self._find_step(workflow, current_step.error_step_id)
                else:
                    current_step = self._find_step(workflow, current_step.next_step_id)

            self.executions[execution_id] = {
                'workflow_id': workflow_id,
                'status': 'completed',
                'results': results,
            }

            return {
                'success': True,
                'execution_id': execution_id,
                'results': results,
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
            }

    def _send_email(self, step: WorkflowStep, context: dict) -> dict:
        """Send email action."""
        try:
            config = step.config
            return {
                'success': True,
                'status': 'sent',
                'to': config.get('to'),
            }
        except Exception as e:
            return {'success': False, 'status': 'failed', 'error': str(e)}

    def _send_sms(self, step: WorkflowStep, context: dict) -> dict:
        """Send SMS action."""
        try:
            config = step.config
            return {
                'success': True,
                'status': 'sent',
                'to': config.get('phone'),
            }
        except Exception as e:
            return {'success': False, 'status': 'failed', 'error': str(e)}

    def _create_task(self, step: WorkflowStep, context: dict) -> dict:
        """Create task action."""
        try:
            config = step.config
            return {
                'success': True,
                'status': 'created',
                'task_id': str(uuid.uuid4()),
            }
        except Exception as e:
            return {'success': False, 'status': 'failed', 'error': str(e)}

    def _update_field(self, step: WorkflowStep, context: dict) -> dict:
        """Update field action."""
        try:
            config = step.config
            return {
                'success': True,
                'status': 'updated',
                'field': config.get('field'),
            }
        except Exception as e:
            return {'success': False, 'status': 'failed', 'error': str(e)}

    def _call_webhook(self, step: WorkflowStep, context: dict) -> dict:
        """Call webhook action."""
        try:
            config = step.config
            return {
                'success': True,
                'status': 'called',
                'url': config.get('url'),
            }
        except Exception as e:
            return {'success': False, 'status': 'failed', 'error': str(e)}

    def _wait(self, step: WorkflowStep, context: dict) -> dict:
        """Wait action."""
        try:
            config = step.config
            return {
                'success': True,
                'status': 'waited',
                'duration': config.get('duration'),
            }
        except Exception as e:
            return {'success': False, 'status': 'failed', 'error': str(e)}

    def _conditional(self, step: WorkflowStep, context: dict) -> dict:
        """Conditional logic."""
        try:
            config = step.config
            condition = config.get('condition')
            # Placeholder: actual condition evaluation
            return {
                'success': True,
                'status': 'evaluated',
            }
        except Exception as e:
            return {'success': False, 'status': 'failed', 'error': str(e)}

    def _loop(self, step: WorkflowStep, context: dict) -> dict:
        """Loop action."""
        try:
            config = step.config
            return {
                'success': True,
                'status': 'looped',
                'iterations': config.get('iterations', 1),
            }
        except Exception as e:
            return {'success': False, 'status': 'failed', 'error': str(e)}

    def _find_step(self, workflow: Workflow, step_id: Optional[str]) -> Optional[WorkflowStep]:
        """Find step by ID."""
        if not step_id:
            return None
        for step in workflow.steps:
            if step.id == step_id:
                return step
        return None

    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Get workflow details."""
        return self.workflows.get(workflow_id)

    def list_workflows(self, user_id: str) -> list[Workflow]:
        """List workflows for user."""
        return [w for w in self.workflows.values() if w.user_id == user_id]

    def delete_workflow(self, workflow_id: str) -> bool:
        """Delete workflow."""
        if workflow_id in self.workflows:
            del self.workflows[workflow_id]
            return True
        return False


# Singleton instance
workflow_engine = WorkflowEngine()
