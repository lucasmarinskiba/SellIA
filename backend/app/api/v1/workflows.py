"""Workflow automation API endpoints."""

from uuid import UUID
from typing import Optional, List, Dict

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.businesses.models import Business
from app.domains.workflows.workflow_engine import WorkflowEngine
from app.domains.workflows.workflow_models import Workflow

router = APIRouter(prefix="/api/v1", tags=["workflows"])


async def _get_business_for_user(business_id: UUID, user: User, db: AsyncSession) -> Business:
    """Same convention as websites.py/catalog.py/channels.py/conversations.py."""
    result = await db.execute(
        select(Business).where(Business.id == business_id, Business.user_id == user.id)
    )
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")
    return business


async def _get_owned_workflow(workflow_id: UUID, user: User, db: AsyncSession) -> Workflow:
    """Look up a workflow by id alone and verify it belongs to a business the
    caller owns. Needed because activate/pause/execute/executions/metrics
    only ever took {workflow_id} in the URL, with no business_id to check
    against -- every one of them worked for any workflow_id, from anyone,
    with no auth at all, before this fix.
    """
    result = await db.execute(
        select(Workflow).where(Workflow.id == workflow_id, Workflow.is_deleted == False)
    )
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow no encontrado")
    await _get_business_for_user(workflow.business_id, user, db)
    return workflow


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
async def create_workflow(
    business_id: UUID,
    request: CreateWorkflowRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create workflow."""
    await _get_business_for_user(business_id, current_user, db)
    conditions = [c.dict() for c in request.conditions] if request.conditions else None
    actions = [a.dict() for a in request.actions] if request.actions else None

    return await WorkflowEngine.create_workflow(
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
async def get_workflows(
    business_id: UUID,
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get workflows."""
    await _get_business_for_user(business_id, current_user, db)
    return await WorkflowEngine.get_workflows(
        business_id=business_id,
        active_only=active_only,
        db=db
    )


@router.post("/workflows/{workflow_id}/activate")
async def activate_workflow(
    workflow_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Activate workflow."""
    workflow = await _get_owned_workflow(workflow_id, current_user, db)
    return await WorkflowEngine.activate_workflow(
        workflow_id=workflow_id,
        business_id=workflow.business_id,
        db=db
    )


@router.post("/workflows/{workflow_id}/pause")
async def pause_workflow(
    workflow_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Pause workflow."""
    workflow = await _get_owned_workflow(workflow_id, current_user, db)
    return await WorkflowEngine.pause_workflow(
        workflow_id=workflow_id,
        business_id=workflow.business_id,
        db=db
    )


@router.post("/workflows/{workflow_id}/execute")
async def execute_workflow(
    workflow_id: UUID,
    request: ExecuteWorkflowRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Execute workflow."""
    workflow = await _get_owned_workflow(workflow_id, current_user, db)
    return await WorkflowEngine.execute_workflow(
        workflow_id=workflow_id,
        business_id=workflow.business_id,
        customer_id=request.customer_id,
        trigger_data=request.trigger_data,
        db=db
    )


@router.get("/workflows/{workflow_id}/executions")
async def get_workflow_executions(
    workflow_id: UUID,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get workflow execution history."""
    workflow = await _get_owned_workflow(workflow_id, current_user, db)
    return await WorkflowEngine.get_workflow_executions(
        workflow_id=workflow_id,
        business_id=workflow.business_id,
        limit=limit,
        db=db
    )


@router.get("/workflows/{workflow_id}/metrics")
async def get_workflow_metrics(
    workflow_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get workflow metrics."""
    workflow = await _get_owned_workflow(workflow_id, current_user, db)
    return await WorkflowEngine.get_workflow_metrics(
        workflow_id=workflow_id,
        business_id=workflow.business_id,
        db=db
    )
