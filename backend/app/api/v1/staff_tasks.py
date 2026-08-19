"""Staff task management API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user
from app.domains.users.models import User
from app.domains.staff.task_service import StaffTaskService, TaskNotificationService, ShiftReadinessService

router = APIRouter(prefix="/api/v1", tags=["staff-tasks"])


class CreateTaskRequest(BaseModel):
    location_id: UUID
    assigned_to_staff_id: UUID
    task_type: str  # demo_setup, visitor_tour, product_demo, follow_up_call, etc
    title: str
    due_date: str  # ISO8601
    description: Optional[str] = None
    priority: str = "medium"
    estimated_duration_minutes: int = 15
    related_checkin_id: Optional[UUID] = None
    related_product_id: Optional[str] = None


class TaskActionRequest(BaseModel):
    task_id: UUID
    completion_notes: Optional[str] = None
    completion_evidence: Optional[dict] = None


@router.post("/tasks/assign")
async def assign_task(
    request: CreateTaskRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Assign task to staff member."""
    try:
        due_date = datetime.fromisoformat(request.due_date.replace('Z', '+00:00'))

        result = StaffTaskService.assign_task(
            location_id=request.location_id,
            business_id=UUID("00000000-0000-0000-0000-000000000000"),  # TODO: from location
            assigned_to_staff_id=request.assigned_to_staff_id,
            task_type=request.task_type,
            title=request.title,
            due_date=due_date,
            description=request.description,
            priority=request.priority,
            estimated_duration_minutes=request.estimated_duration_minutes,
            related_checkin_id=request.related_checkin_id,
            related_product_id=request.related_product_id,
            assigned_by_staff_id=current_user.id,
            db=db
        )

        # Send notification
        TaskNotificationService.notify_task_assigned(
            task_id=UUID(result["task_id"]),
            staff_id=request.assigned_to_staff_id,
            db=db
        )

        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/staff/{staff_id}/tasks")
async def get_staff_tasks(
    staff_id: UUID,
    location_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> dict:
    """Get tasks assigned to staff."""
    try:
        tasks = StaffTaskService.get_staff_tasks(
            staff_id=staff_id,
            location_id=location_id,
            status_filter=status,
            db=db
        )

        task_list = [
            {
                "task_id": str(t.id),
                "title": t.title,
                "task_type": t.task_type.value,
                "priority": t.priority.value,
                "status": t.status.value,
                "due_date": t.due_date.isoformat(),
                "description": t.description,
                "estimated_duration_minutes": t.estimated_duration_minutes,
                "assigned_at": t.assigned_at.isoformat(),
                "acknowledged_at": t.acknowledged_at.isoformat() if t.acknowledged_at else None,
                "started_at": t.started_at.isoformat() if t.started_at else None,
            }
            for t in tasks
        ]

        return {
            "staff_id": str(staff_id),
            "total_tasks": len(task_list),
            "tasks": task_list
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/tasks/{task_id}/acknowledge")
async def acknowledge_task(
    task_id: UUID,
    db: Session = Depends(get_db),
) -> dict:
    """Staff acknowledges task assignment."""
    try:
        result = StaffTaskService.acknowledge_task(task_id=task_id, db=db)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/tasks/{task_id}/start")
async def start_task(
    task_id: UUID,
    db: Session = Depends(get_db),
) -> dict:
    """Mark task as in-progress."""
    try:
        result = StaffTaskService.start_task(task_id=task_id, db=db)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/tasks/{task_id}/complete")
async def complete_task(
    task_id: UUID,
    request: TaskActionRequest,
    db: Session = Depends(get_db),
) -> dict:
    """Mark task as completed."""
    try:
        result = StaffTaskService.complete_task(
            task_id=request.task_id,
            completion_notes=request.completion_notes,
            completion_evidence=request.completion_evidence,
            db=db
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/tasks/{task_id}/cancel")
async def cancel_task(
    task_id: UUID,
    reason: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> dict:
    """Cancel task."""
    try:
        result = StaffTaskService.cancel_task(task_id=task_id, reason=reason, db=db)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/locations/{location_id}/task-queue")
async def get_location_task_queue(
    location_id: UUID,
    max_results: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
) -> dict:
    """Get pending tasks for location."""
    try:
        result = StaffTaskService.get_task_queue(
            location_id=location_id,
            max_results=max_results,
            db=db
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/staff/{staff_id}/tasks/auto-assign")
async def auto_assign_shift_tasks(
    staff_id: UUID,
    location_id: UUID,
    shift_start: str,  # ISO8601
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Auto-assign pending tasks to staff for shift."""
    try:
        shift_start_dt = datetime.fromisoformat(shift_start.replace('Z', '+00:00'))

        result = StaffTaskService.auto_assign_tasks_to_shift(
            location_id=location_id,
            staff_id=staff_id,
            shift_start=shift_start_dt,
            db=db
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tasks/{task_id}/notifications")
async def get_task_notifications(
    task_id: UUID,
    db: Session = Depends(get_db),
) -> dict:
    """Get notification history for task."""
    try:
        from app.domains.staff.task_models import TaskNotification

        notifications = db.query(TaskNotification).filter(
            TaskNotification.task_id == task_id
        ).all()

        notif_list = [
            {
                "notification_id": str(n.id),
                "type": n.notification_type,
                "sent_at": n.sent_at.isoformat(),
                "read_at": n.read_at.isoformat() if n.read_at else None,
                "delivery_status": n.delivery_status,
            }
            for n in notifications
        ]

        return {
            "task_id": str(task_id),
            "notifications": notif_list
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: UUID,
    db: Session = Depends(get_db),
) -> dict:
    """Mark notification as read."""
    try:
        result = TaskNotificationService.mark_notification_read(
            notification_id=notification_id,
            db=db
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/staff/{staff_id}/shift-report")
async def get_shift_readiness_report(
    staff_id: UUID,
    location_id: UUID,
    shift_start: str,  # ISO8601
    shift_end: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> dict:
    """Generate shift readiness report."""
    try:
        shift_start_dt = datetime.fromisoformat(shift_start.replace('Z', '+00:00'))
        shift_end_dt = None
        if shift_end:
            shift_end_dt = datetime.fromisoformat(shift_end.replace('Z', '+00:00'))

        result = ShiftReadinessService.generate_shift_report(
            location_id=location_id,
            business_id=UUID("00000000-0000-0000-0000-000000000000"),  # TODO: from location
            staff_id=staff_id,
            shift_start=shift_start_dt,
            shift_end=shift_end_dt,
            db=db
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/staff/{staff_id}/performance")
async def get_staff_performance(
    staff_id: UUID,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
) -> dict:
    """Get staff task performance metrics."""
    try:
        result = ShiftReadinessService.get_staff_performance(
            staff_id=staff_id,
            days=days,
            db=db
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
