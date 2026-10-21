"""Staff task API endpoints.

Who may do what (see app.core.business_access):

* assign / cancel / auto-assign tasks, read another person's tasks, shift report or
  performance -> the owner or an ADMIN member of the task's business;
* acknowledge / start / complete a task, read its notifications, mark one read ->
  the person it is assigned to (while still part of the business) or a manager;
* read a location's task queue -> any member.

The services are sync (Session.query / commit) while get_db yields an AsyncSession, so
every DB touch runs inside ``await db.run_sync(...)``. Access checks run before the try
block: a 403/404 must not be turned into a 400 by the broad except.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.business_access import (
    is_business_participant,
    require_business_access,
    require_location_access,
    staff_scope,
)
from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.staff.task_models import StaffTask, TaskNotification
from app.domains.staff.task_service import StaffTaskService, TaskNotificationService, ShiftReadinessService
from app.domains.users.models import User

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


async def _get_task(db: AsyncSession, task_id: UUID) -> StaffTask:
    task = await db.get(StaffTask, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    return task


async def _require_task_actor(db: AsyncSession, task: StaffTask, user: User) -> None:
    """The assignee (while still in the business) or a manager of the task's business."""
    if task.assigned_to_staff_id == user.id:
        await require_business_access(db, task.business_id, user)
    else:
        await require_business_access(db, task.business_id, user, manage=True)


@router.post("/tasks/assign")
async def assign_task(
    request: CreateTaskRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Assign task to staff member."""
    location = await require_location_access(db, request.location_id, current_user, manage=True)
    business_id = location.business_id
    if not await is_business_participant(db, business_id, request.assigned_to_staff_id):
        raise HTTPException(status_code=400, detail="La persona asignada no pertenece a este negocio")

    def _assign(sync_db: Session) -> dict:
        due_date = datetime.fromisoformat(request.due_date.replace('Z', '+00:00'))

        result = StaffTaskService.assign_task(
            location_id=request.location_id,
            business_id=business_id,
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
            db=sync_db
        )

        # Send notification
        TaskNotificationService.notify_task_assigned(
            task_id=UUID(result["task_id"]),
            staff_id=request.assigned_to_staff_id,
            db=sync_db
        )

        return result

    try:
        return await db.run_sync(_assign)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/staff/{staff_id}/tasks")
async def get_staff_tasks(
    staff_id: UUID,
    location_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get tasks assigned to staff."""
    scope = await staff_scope(db, staff_id, current_user)
    if location_id is not None:
        await require_location_access(db, location_id, current_user, manage=staff_id != current_user.id)

    try:
        tasks = await db.run_sync(
            lambda sync_db: StaffTaskService.get_staff_tasks(
                staff_id=staff_id,
                location_id=location_id,
                status_filter=status,
                db=sync_db
            )
        )
        tasks = [t for t in tasks if t.business_id in scope]

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
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Staff acknowledges task assignment."""
    await _require_task_actor(db, await _get_task(db, task_id), current_user)

    try:
        return await db.run_sync(lambda sync_db: StaffTaskService.acknowledge_task(task_id=task_id, db=sync_db))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/tasks/{task_id}/start")
async def start_task(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Mark task as in-progress."""
    await _require_task_actor(db, await _get_task(db, task_id), current_user)

    try:
        return await db.run_sync(lambda sync_db: StaffTaskService.start_task(task_id=task_id, db=sync_db))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/tasks/{task_id}/complete")
async def complete_task(
    task_id: UUID,
    request: TaskActionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Mark task as completed."""
    # The service used the body's id while the path's id was what got authorised.
    if request.task_id != task_id:
        raise HTTPException(status_code=400, detail="task_id del path y del body no coinciden")
    await _require_task_actor(db, await _get_task(db, task_id), current_user)

    try:
        return await db.run_sync(
            lambda sync_db: StaffTaskService.complete_task(
                task_id=task_id,
                completion_notes=request.completion_notes,
                completion_evidence=request.completion_evidence,
                db=sync_db
            )
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/tasks/{task_id}/cancel")
async def cancel_task(
    task_id: UUID,
    reason: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Cancel task."""
    task = await _get_task(db, task_id)
    await require_business_access(db, task.business_id, current_user, manage=True)

    try:
        return await db.run_sync(
            lambda sync_db: StaffTaskService.cancel_task(task_id=task_id, reason=reason, db=sync_db)
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/locations/{location_id}/task-queue")
async def get_location_task_queue(
    location_id: UUID,
    max_results: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get pending tasks for location."""
    await require_location_access(db, location_id, current_user)

    try:
        return await db.run_sync(
            lambda sync_db: StaffTaskService.get_task_queue(
                location_id=location_id,
                max_results=max_results,
                db=sync_db
            )
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/staff/{staff_id}/tasks/auto-assign")
async def auto_assign_shift_tasks(
    staff_id: UUID,
    location_id: UUID,
    shift_start: str,  # ISO8601
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Auto-assign pending tasks to staff for shift."""
    location = await require_location_access(db, location_id, current_user, manage=True)
    if not await is_business_participant(db, location.business_id, staff_id):
        raise HTTPException(status_code=400, detail="La persona asignada no pertenece a este negocio")

    try:
        shift_start_dt = datetime.fromisoformat(shift_start.replace('Z', '+00:00'))

        return await db.run_sync(
            lambda sync_db: StaffTaskService.auto_assign_tasks_to_shift(
                location_id=location_id,
                staff_id=staff_id,
                shift_start=shift_start_dt,
                db=sync_db
            )
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tasks/{task_id}/notifications")
async def get_task_notifications(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get notification history for task."""
    await _require_task_actor(db, await _get_task(db, task_id), current_user)

    try:
        def _load(sync_db: Session) -> list:
            return sync_db.query(TaskNotification).filter(TaskNotification.task_id == task_id).all()

        notifications = await db.run_sync(_load)

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
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Mark notification as read."""
    notification = await db.get(TaskNotification, notification_id)
    if notification is None:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    # "Read" is the recipient's own receipt (a manager may see the history, not sign for it).
    if notification.staff_id != current_user.id:
        raise HTTPException(status_code=403, detail="Solo quien recibió la notificación puede marcarla como leída")
    task = await _get_task(db, notification.task_id)
    await require_business_access(db, task.business_id, current_user)

    try:
        return await db.run_sync(
            lambda sync_db: TaskNotificationService.mark_notification_read(
                notification_id=notification_id,
                db=sync_db
            )
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/staff/{staff_id}/shift-report")
async def get_shift_readiness_report(
    staff_id: UUID,
    location_id: UUID,
    shift_start: str,  # ISO8601
    shift_end: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Generate shift readiness report."""
    location = await require_location_access(db, location_id, current_user, manage=staff_id != current_user.id)
    business_id = location.business_id

    try:
        shift_start_dt = datetime.fromisoformat(shift_start.replace('Z', '+00:00'))
        shift_end_dt = None
        if shift_end:
            shift_end_dt = datetime.fromisoformat(shift_end.replace('Z', '+00:00'))

        return await db.run_sync(
            lambda sync_db: ShiftReadinessService.generate_shift_report(
                location_id=location_id,
                business_id=business_id,
                staff_id=staff_id,
                shift_start=shift_start_dt,
                shift_end=shift_end_dt,
                db=sync_db
            )
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Not "/staff/{staff_id}/performance": location_checkin already mounts that exact path (check-in
# stats) and would shadow this one.
@router.get("/staff/{staff_id}/task-performance")
async def get_staff_task_performance(
    staff_id: UUID,
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get staff task performance metrics."""
    scope = await staff_scope(db, staff_id, current_user)

    try:
        return await db.run_sync(
            lambda sync_db: ShiftReadinessService.get_staff_performance(
                staff_id=staff_id,
                days=days,
                db=sync_db,
                business_ids=scope
            )
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
