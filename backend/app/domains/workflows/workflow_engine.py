"""Workflow automation engine."""

import logging
from datetime import datetime, timezone
from uuid import UUID
from typing import Optional, Dict, List

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.workflows.workflow_models import (
    Workflow, WorkflowCondition, WorkflowAction, WorkflowExecution,
    WorkflowMetrics, TriggerType, ActionType, ConditionOperator
)

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """Workflow automation engine.

    Was written entirely against the legacy sync SQLAlchemy Session API
    (db.query(...).filter(...).first(), bare db.commit()/db.refresh() with
    no await) while api/v1/workflows.py injects the app's real, fully-async
    AsyncSession via Depends(get_db). AsyncSession has no .query() method at
    all, so every read here (get_workflows, activate_workflow,
    execute_workflow, get_workflow_executions, get_workflow_metrics) would
    raise AttributeError on first real use; the one write path that reaches
    db.commit()/db.refresh() without erroring first (create_workflow) would
    silently no-op, since those calls return unawaited coroutines on an
    AsyncSession. This entire feature has been non-functional in production
    independent of the auth issue this file was originally being fixed for.
    Ported to the real async API throughout.
    """

    @staticmethod
    async def create_workflow(
        business_id: UUID,
        name: str,
        description: str,
        trigger_type: str,
        trigger_config: dict,
        conditions: Optional[List[dict]] = None,
        actions: Optional[List[dict]] = None,
        db: AsyncSession = None
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
        await db.commit()
        await db.refresh(workflow)

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

        await db.commit()

        # Create metrics record
        metrics = WorkflowMetrics(
            business_id=business_id,
            workflow_id=workflow.id
        )
        db.add(metrics)
        await db.commit()

        logger.info(f"Workflow created: {name} ({trigger_type})")

        return {
            "workflow_id": str(workflow.id),
            "name": name,
            "trigger_type": trigger_type,
            "is_active": workflow.is_active
        }

    @staticmethod
    async def get_workflows(
        business_id: UUID,
        active_only: bool = True,
        db: AsyncSession = None
    ) -> List[dict]:
        """Get workflows."""
        if not db:
            raise ValueError("Database session required")

        query = select(Workflow).where(
            Workflow.business_id == business_id,
            Workflow.is_deleted == False
        )

        if active_only:
            query = query.where(Workflow.is_active == True)

        result = await db.execute(query)
        workflows = result.scalars().all()

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
    async def activate_workflow(
        workflow_id: UUID,
        business_id: UUID,
        db: AsyncSession = None
    ) -> dict:
        """Activate workflow."""
        if not db:
            raise ValueError("Database session required")

        result = await db.execute(
            select(Workflow).where(Workflow.id == workflow_id, Workflow.business_id == business_id)
        )
        workflow = result.scalar_one_or_none()
        if not workflow:
            raise ValueError("Workflow not found")

        workflow.is_active = True
        await db.commit()

        return {"workflow_id": str(workflow_id), "is_active": True}

    @staticmethod
    async def pause_workflow(
        workflow_id: UUID,
        business_id: UUID,
        db: AsyncSession = None
    ) -> dict:
        """Pause workflow."""
        if not db:
            raise ValueError("Database session required")

        result = await db.execute(
            select(Workflow).where(Workflow.id == workflow_id, Workflow.business_id == business_id)
        )
        workflow = result.scalar_one_or_none()
        if not workflow:
            raise ValueError("Workflow not found")

        workflow.is_active = False
        await db.commit()

        return {"workflow_id": str(workflow_id), "is_active": False}

    @staticmethod
    async def execute_workflow(
        workflow_id: UUID,
        business_id: UUID,
        customer_id: UUID,
        trigger_data: dict,
        db: AsyncSession = None
    ) -> dict:
        """Execute workflow for customer."""
        if not db:
            raise ValueError("Database session required")

        result = await db.execute(
            select(Workflow).where(
                Workflow.id == workflow_id,
                Workflow.business_id == business_id,
                Workflow.is_active == True,
            )
        )
        workflow = result.scalar_one_or_none()

        if not workflow:
            return {"status": "workflow_not_found"}

        # Check execution limits
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        count_result = await db.execute(
            select(func.count(WorkflowExecution.id)).where(
                WorkflowExecution.workflow_id == workflow_id,
                WorkflowExecution.started_at >= today_start,
            )
        )
        executions_today = count_result.scalar() or 0

        if workflow.max_executions_per_day > 0 and executions_today >= workflow.max_executions_per_day:
            return {"status": "execution_limit_reached"}

        # Evaluate conditions
        conditions_met = await WorkflowEngine._evaluate_conditions(workflow_id, trigger_data, db)
        if not conditions_met:
            return {"status": "conditions_not_met"}

        # Execute actions
        actions_result = await db.execute(
            select(WorkflowAction).where(WorkflowAction.workflow_id == workflow_id).order_by(WorkflowAction.order)
        )
        actions = actions_result.scalars().all()

        execution_log = []
        actions_executed = 0
        actions_failed = 0

        for action in actions:
            result = WorkflowEngine._execute_action(
                action.action_type,
                action.action_config,
                customer_id,
                trigger_data,
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
        metrics_result = await db.execute(
            select(WorkflowMetrics).where(WorkflowMetrics.workflow_id == workflow_id)
        )
        metrics = metrics_result.scalar_one_or_none()

        if metrics:
            metrics.total_executions += 1
            metrics.successful_executions += 1 if actions_failed == 0 else 0
            metrics.failed_executions += 1 if actions_failed > 0 else 0
            metrics.total_actions_executed += actions_executed

        await db.commit()

        logger.info(f"Workflow {workflow_id} executed for customer {customer_id}: {actions_executed} actions")

        return {
            "execution_id": str(execution.id),
            "status": "success",
            "actions_executed": actions_executed,
            "actions_failed": actions_failed
        }

    @staticmethod
    async def _evaluate_conditions(
        workflow_id: UUID,
        trigger_data: dict,
        db: AsyncSession
    ) -> bool:
        """Evaluate workflow conditions."""
        result = await db.execute(
            select(WorkflowCondition).where(WorkflowCondition.workflow_id == workflow_id)
        )
        conditions = result.scalars().all()

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
    async def get_workflow_executions(
        workflow_id: UUID,
        business_id: UUID,
        limit: int = 50,
        db: AsyncSession = None
    ) -> List[dict]:
        """Get workflow execution history."""
        if not db:
            raise ValueError("Database session required")

        result = await db.execute(
            select(WorkflowExecution)
            .where(WorkflowExecution.workflow_id == workflow_id, WorkflowExecution.business_id == business_id)
            .order_by(desc(WorkflowExecution.started_at))
            .limit(limit)
        )
        executions = result.scalars().all()

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
    async def get_workflow_metrics(
        workflow_id: UUID,
        business_id: UUID,
        db: AsyncSession = None
    ) -> dict:
        """Get workflow metrics."""
        if not db:
            raise ValueError("Database session required")

        result = await db.execute(
            select(WorkflowMetrics).where(
                WorkflowMetrics.workflow_id == workflow_id, WorkflowMetrics.business_id == business_id
            )
        )
        metrics = result.scalar_one_or_none()

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
