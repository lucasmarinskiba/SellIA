"""Workflow automation engine."""

import logging
from datetime import datetime, timezone, timedelta
from uuid import UUID
from typing import Optional, Dict, List

from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.domains.workflows.workflow_models import (
    Workflow, WorkflowCondition, WorkflowAction, WorkflowExecution,
    WorkflowMetrics, TriggerType, ActionType, ConditionOperator
)

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """Workflow automation engine."""

    @staticmethod
    def create_workflow(
        business_id: UUID,
        name: str,
        description: str,
        trigger_type: str,
        trigger_config: dict,
        conditions: Optional[List[dict]] = None,
        actions: Optional[List[dict]] = None,
        db: Session = None
    ) -> dict:
        """Create workflow."""
        if not db:
            raise ValueError("Database session required")

        workflow = Workflow(
            business_id=business_id,
            name=name,
            description=description,
            trigger_type=trigger_type,
            trigger_config=trigger_config
        )

        db.add(workflow)
        db.commit()
        db.refresh(workflow)

        # Add conditions
        if conditions:
            for i, cond in enumerate(conditions):
                condition = WorkflowCondition(
                    workflow_id=workflow.id,
                    field_name=cond.get("field_name"),
                    operator=cond.get("operator"),
                    value=cond.get("value"),
                    value_type=cond.get("value_type", "string"),
                    logic_operator=cond.get("logic_operator", "AND")
                )
                db.add(condition)

        # Add actions
        if actions:
            for i, action in enumerate(actions):
                workflow_action = WorkflowAction(
                    workflow_id=workflow.id,
                    action_type=action.get("action_type"),
                    action_config=action.get("action_config", {}),
                    order=i
                )
                db.add(workflow_action)

        db.commit()

        # Create metrics record
        metrics = WorkflowMetrics(
            business_id=business_id,
            workflow_id=workflow.id
        )
        db.add(metrics)
        db.commit()

        logger.info(f"Workflow created: {name} ({trigger_type})")

        return {
            "workflow_id": str(workflow.id),
            "name": name,
            "trigger_type": trigger_type,
            "is_active": workflow.is_active
        }

    @staticmethod
    def get_workflows(
        business_id: UUID,
        active_only: bool = True,
        db: Session = None
    ) -> List[dict]:
        """Get workflows."""
        if not db:
            raise ValueError("Database session required")

        query = db.query(Workflow).filter(
            Workflow.business_id == business_id,
            Workflow.is_deleted == False
        )

        if active_only:
            query = query.filter(Workflow.is_active == True)

        workflows = query.all()

        return [
            {
                "workflow_id": str(w.id),
                "name": w.name,
                "trigger_type": w.trigger_type,
                "is_active": w.is_active,
                "total_executions": w.total_executions,
                "last_executed": w.last_executed_at.isoformat() if w.last_executed_at else None,
            }
            for w in workflows
        ]

    @staticmethod
    def activate_workflow(
        workflow_id: UUID,
        db: Session = None
    ) -> dict:
        """Activate workflow."""
        if not db:
            raise ValueError("Database session required")

        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow:
            raise ValueError("Workflow not found")

        workflow.is_active = True
        db.commit()

        return {"workflow_id": str(workflow_id), "is_active": True}

    @staticmethod
    def pause_workflow(
        workflow_id: UUID,
        db: Session = None
    ) -> dict:
        """Pause workflow."""
        if not db:
            raise ValueError("Database session required")

        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow:
            raise ValueError("Workflow not found")

        workflow.is_active = False
        db.commit()

        return {"workflow_id": str(workflow_id), "is_active": False}

    @staticmethod
    def execute_workflow(
        workflow_id: UUID,
        customer_id: UUID,
        trigger_data: dict,
        db: Session = None
    ) -> dict:
        """Execute workflow for customer."""
        if not db:
            raise ValueError("Database session required")

        workflow = db.query(Workflow).filter(
            Workflow.id == workflow_id,
            Workflow.is_active == True
        ).first()

        if not workflow:
            return {"status": "workflow_not_found"}

        # Check execution limits
        executions_today = db.query(func.count(WorkflowExecution.id)).filter(
            WorkflowExecution.workflow_id == workflow_id,
            WorkflowExecution.started_at >= datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        ).scalar() or 0

        if workflow.max_executions_per_day > 0 and executions_today >= workflow.max_executions_per_day:
            return {"status": "execution_limit_reached"}

        # Evaluate conditions
        conditions_met = WorkflowEngine._evaluate_conditions(workflow_id, trigger_data, db)
        if not conditions_met:
            return {"status": "conditions_not_met"}

        # Execute actions
        actions = db.query(WorkflowAction).filter(
            WorkflowAction.workflow_id == workflow_id
        ).order_by(WorkflowAction.order).all()

        execution_log = []
        actions_executed = 0
        actions_failed = 0

        for action in actions:
            result = WorkflowEngine._execute_action(
                action.action_type,
                action.action_config,
                customer_id,
                trigger_data,
                db
            )
            execution_log.append(result)
            if result.get("status") == "success":
                actions_executed += 1
            else:
                actions_failed += 1

        # Log execution
        execution = WorkflowExecution(
            workflow_id=workflow_id,
            business_id=workflow.business_id,
            customer_id=customer_id,
            trigger_type=workflow.trigger_type,
            trigger_data=trigger_data,
            execution_status="success" if actions_failed == 0 else "partial_failure",
            actions_executed=actions_executed,
            actions_failed=actions_failed,
            execution_log=execution_log,
            completed_at=datetime.now(timezone.utc)
        )

        db.add(execution)

        # Update workflow stats
        workflow.total_executions += 1
        if actions_failed > 0:
            workflow.total_failures += 1
        workflow.last_executed_at = datetime.now(timezone.utc)

        # Update metrics
        metrics = db.query(WorkflowMetrics).filter(
            WorkflowMetrics.workflow_id == workflow_id
        ).first()

        if metrics:
            metrics.total_executions += 1
            metrics.successful_executions += 1 if actions_failed == 0 else 0
            metrics.failed_executions += 1 if actions_failed > 0 else 0
            metrics.total_actions_executed += actions_executed

        db.commit()

        logger.info(f"Workflow {workflow_id} executed for customer {customer_id}: {actions_executed} actions")

        return {
            "execution_id": str(execution.id),
            "status": "success",
            "actions_executed": actions_executed,
            "actions_failed": actions_failed
        }

    @staticmethod
    def _evaluate_conditions(
        workflow_id: UUID,
        trigger_data: dict,
        db: Session
    ) -> bool:
        """Evaluate workflow conditions."""
        conditions = db.query(WorkflowCondition).filter(
            WorkflowCondition.workflow_id == workflow_id
        ).all()

        if not conditions:
            return True  # No conditions = always execute

        # Placeholder: implement condition evaluation logic
        # In production would check customer scores, segment membership, etc.
        return True

    @staticmethod
    def _execute_action(
        action_type: str,
        action_config: dict,
        customer_id: UUID,
        trigger_data: dict,
        db: Session
    ) -> dict:
        """Execute single workflow action."""
        try:
            if action_type == ActionType.SEND_EMAIL.value:
                # Placeholder: send email via connector
                return {"action_type": action_type, "status": "success"}
            elif action_type == ActionType.SEND_SMS.value:
                # Placeholder: send SMS
                return {"action_type": action_type, "status": "success"}
            elif action_type == ActionType.ADD_TO_SEGMENT.value:
                # Placeholder: add customer to segment
                return {"action_type": action_type, "status": "success"}
            elif action_type == ActionType.CREATE_TASK.value:
                # Placeholder: create task
                return {"action_type": action_type, "status": "success"}
            else:
                return {"action_type": action_type, "status": "unknown_action"}

        except Exception as e:
            logger.error(f"Action execution failed: {action_type} - {str(e)}")
            return {"action_type": action_type, "status": "failed", "error": str(e)}

    @staticmethod
    def get_workflow_executions(
        workflow_id: UUID,
        limit: int = 50,
        db: Session = None
    ) -> List[dict]:
        """Get workflow execution history."""
        if not db:
            raise ValueError("Database session required")

        executions = db.query(WorkflowExecution).filter(
            WorkflowExecution.workflow_id == workflow_id
        ).order_by(desc(WorkflowExecution.started_at)).limit(limit).all()

        return [
            {
                "execution_id": str(e.id),
                "customer_id": str(e.customer_id) if e.customer_id else None,
                "status": e.execution_status,
                "actions_executed": e.actions_executed,
                "actions_failed": e.actions_failed,
                "started_at": e.started_at.isoformat(),
                "completed_at": e.completed_at.isoformat() if e.completed_at else None,
            }
            for e in executions
        ]

    @staticmethod
    def get_workflow_metrics(
        workflow_id: UUID,
        db: Session = None
    ) -> dict:
        """Get workflow metrics."""
        if not db:
            raise ValueError("Database session required")

        metrics = db.query(WorkflowMetrics).filter(
            WorkflowMetrics.workflow_id == workflow_id
        ).first()

        if not metrics:
            return {"message": "No metrics found"}

        return {
            "total_executions": metrics.total_executions,
            "successful_executions": metrics.successful_executions,
            "failed_executions": metrics.failed_executions,
            "skipped_executions": metrics.skipped_executions,
            "avg_execution_time_ms": metrics.avg_execution_time_ms,
            "total_actions_executed": metrics.total_actions_executed,
            "error_count": metrics.error_count,
            "executions_7d": metrics.executions_7d,
            "success_rate_7d": metrics.success_rate_7d,
        }
