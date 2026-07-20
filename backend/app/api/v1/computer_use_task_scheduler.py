"""Task Scheduler API Router

Endpoints para gestionar task queue:
- POST /tasks/enqueue — encolar tarea
- GET /tasks/queue-status — ver estado de queue
- GET /tasks/history — historial de tareas
"""

import logging
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.core.logger import get_logger
from app.domains.users.models import User
from app.domains.computer_use.services.task_scheduler import (
    get_task_scheduler,
    TaskType,
    TaskPriority,
)

logger = get_logger(__name__)
router = APIRouter()


# ========== Models ==========


class EnqueueTaskRequest(BaseModel):
    """Request para encolar tarea."""

    task_type: str = Field(..., description="respond_message, schedule_appointment, close_sale, launch_ad_campaign, etc")
    customer_id: Optional[str] = None
    payload: dict = Field(..., description="Task-specific data")
    priority: Optional[str] = None  # urgent, high, medium, low, batch
    due_at: Optional[str] = None  # ISO datetime


class TaskResponse(BaseModel):
    """Respuesta con detalles de tarea."""

    task_id: str
    task_type: str
    priority: str
    status: str
    due_at: Optional[str]
    created_at: str
    retry_count: int


class QueueStatusResponse(BaseModel):
    """Status de la queue."""

    pending_count: int
    pending_by_priority: dict
    executing_count: int
    completed_count: int
    total_capacity: int


# ========== Endpoints ==========


@router.post("/tasks/enqueue", response_model=TaskResponse)
async def enqueue_task(
    request: EnqueueTaskRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Encola tarea con validación automática de conflictos.

    Tipos de tareas:
    - respond_message: Responder mensaje de cliente (URGENT)
    - schedule_appointment: Agendar cita (HIGH)
    - close_sale: Cerrar venta (HIGH)
    - launch_ad_campaign: Lanzar ads (MEDIUM)
    - send_follow_up: Follow-up (MEDIUM)
    - nurture_lead: Nurture (LOW)
    - re_engagement: Re-engagement (LOW)
    - handle_objection: Manejar objeción (URGENT)
    """
    try:
        # Validar task_type
        try:
            task_type = TaskType(request.task_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid task_type. Valid: {', '.join([t.value for t in TaskType])}",
            )

        # Parsear priority
        priority = None
        if request.priority:
            try:
                priority = TaskPriority[request.priority.upper()]
            except KeyError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid priority. Valid: {', '.join([p.name.lower() for p in TaskPriority])}",
                )

        # Parsear due_at
        due_at = None
        if request.due_at:
            try:
                due_at = datetime.fromisoformat(request.due_at)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid due_at format (use ISO)")

        # Encolar
        scheduler = get_task_scheduler()
        task_id, success, conflict_reason = await scheduler.enqueue_task(
            task_type=task_type,
            user_id=str(current_user.id),
            payload=request.payload,
            priority=priority,
            customer_id=request.customer_id,
            due_at=due_at,
        )

        if not success and conflict_reason:
            raise HTTPException(
                status_code=409,
                detail=f"Task conflict: {conflict_reason}. Will be scheduled later.",
            )

        # Obtener task para response
        task = next(
            (t for t in scheduler.task_queue if t.task_id == task_id),
            None,
        )

        if task:
            return TaskResponse(
                task_id=task.task_id,
                task_type=task.task_type.value,
                priority=task.priority.name,
                status=task.status,
                due_at=task.due_at.isoformat() if task.due_at else None,
                created_at=task.created_at.isoformat(),
                retry_count=task.retry_count,
            )

        raise HTTPException(status_code=500, detail="Task not found after enqueue")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enqueuing task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/queue-status", response_model=QueueStatusResponse)
async def get_queue_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retorna estado actual de task queue."""
    try:
        scheduler = get_task_scheduler()
        status = await scheduler.get_queue_status()

        return QueueStatusResponse(**status)

    except Exception as e:
        logger.error(f"Error getting queue status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/info")
async def get_task_info(
    current_user: User = Depends(get_current_active_user),
):
    """Retorna info sobre tipos de tareas y prioridades."""
    return {
        "task_types": {
            "respond_message": {"description": "Respond to customer message", "default_priority": "URGENT"},
            "schedule_appointment": {"description": "Schedule meeting/call", "default_priority": "HIGH"},
            "close_sale": {"description": "Execute closing sequence", "default_priority": "HIGH"},
            "launch_ad_campaign": {"description": "Launch advertising campaign", "default_priority": "MEDIUM"},
            "send_follow_up": {"description": "Send follow-up to lead", "default_priority": "MEDIUM"},
            "nurture_lead": {"description": "Nurture lead with content", "default_priority": "LOW"},
            "re_engagement": {"description": "Re-engage cold lead", "default_priority": "LOW"},
            "handle_objection": {"description": "Address customer objection", "default_priority": "URGENT"},
        },
        "priorities": {
            "URGENT": 1,
            "HIGH": 2,
            "MEDIUM": 3,
            "LOW": 4,
            "BATCH": 5,
        },
        "limits": {
            "max_concurrent_tasks": 10,
            "max_tasks_per_customer_per_hour": 5,
            "retry_max_attempts": 3,
            "retry_backoff": "exponential (2^n seconds)",
        },
        "conflict_resolution": [
            "Too many tasks per customer → reschedule to 1 hour later",
            "Conflicting task types running → queue until previous completes",
        ],
    }
