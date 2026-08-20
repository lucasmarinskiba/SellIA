"""Workflow automation API endpoints."""

from uuid import UUID
from typing import Optional, List, Dict

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.domains.workflows.workflow_engine import WorkflowEngine

router = APIRouter(prefix="/api/v1", tags=["workflows"])


class WorkflowConditionRequest(BaseModel):
    field_name: str
    operator: str
    value: Optional[str] = None
    value_type: Optional[str] = "string"
    logic_operator: Optional[str] = "AND"


class WorkflowActionRequest(BaseModel):
    action_type: str
    action_config: Dict
    run_after_delay: Optional[int] = 0


class CreateWorkflowRequest(BaseModel):
    name: str
    description: Optional[str] = None
    trigger_type: str
    trigger_config: Dict
    conditions: Optional[List[WorkflowConditionRequest]] = None
    actions: Optional[List[WorkflowActionRequest]] = None


class ExecuteWorkflowRequest(BaseModel):
    customer_id: UUID
    trigger_data: Dict


@router.post("/businesses/{business_id}/workflows")
def create_workflow(
    business_id: UUID,
    request: CreateWorkflowRequest,
    db: Session = Depends(get_db)
):
    """Create workflow."""
    conditions = [c.dict() for c in request.conditions] if request.conditions else None
    actions = [a.dict() for a in request.actions] if request.actions else None

    return WorkflowEngine.create_workflow(
        business_id=business_id,
        name=request.name,
        description=request.description,
        trigger_type=request.trigger_type,
        trigger_config=request.trigger_config,
        conditions=conditions,
        actions=actions,
        db=db
    )


@router.get("/businesses/{business_id}/workflows")
def get_workflows(
    business_id: UUID,
    active_only: bool = Query(True),
    db: Session = Depends(get_db)
):
    """Get workflows."""
    return WorkflowEngine.get_workflows(
        business_id=business_id,
        active_only=active_only,
        db=db
    )


@router.post("/workflows/{workflow_id}/activate")
def activate_workflow(
    workflow_id: UUID,
    db: Session = Depends(get_db)
):
    """Activate workflow."""
    return WorkflowEngine.activate_workflow(
        workflow_id=workflow_id,
        db=db
    )


@router.post("/workflows/{workflow_id}/pause")
def pause_workflow(
    workflow_id: UUID,
    db: Session = Depends(get_db)
):
    """Pause workflow."""
    return WorkflowEngine.pause_workflow(
        workflow_id=workflow_id,
        db=db
    )


@router.post("/workflows/{workflow_id}/execute")
def execute_workflow(
    workflow_id: UUID,
    request: ExecuteWorkflowRequest,
    db: Session = Depends(get_db)
):
    """Execute workflow."""
    return WorkflowEngine.execute_workflow(
        workflow_id=workflow_id,
        customer_id=request.customer_id,
        trigger_data=request.trigger_data,
        db=db
    )


@router.get("/workflows/{workflow_id}/executions")
def get_workflow_executions(
    workflow_id: UUID,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Get workflow execution history."""
    return WorkflowEngine.get_workflow_executions(
        workflow_id=workflow_id,
        limit=limit,
        db=db
    )


@router.get("/workflows/{workflow_id}/metrics")
def get_workflow_metrics(
    workflow_id: UUID,
    db: Session = Depends(get_db)
):
    """Get workflow metrics."""
    return WorkflowEngine.get_workflow_metrics(
        workflow_id=workflow_id,
        db=db
    )
