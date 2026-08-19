"""Staff task service — assignment, dispatch, completion tracking."""

import logging
from datetime import datetime, timezone, timedelta
from uuid import UUID
from typing import Optional, List

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.domains.staff.task_models import (
    StaffTask, TaskNotification, TaskTemplate, ShiftReadinessReport,
    TaskStatus, TaskPriority, TaskType
)

logger = logging.getLogger(__name__)


class StaffTaskService:
    """Manage tasks for staff."""

    @staticmethod
    def assign_task(
        location_id: UUID,
        business_id: UUID,
        assigned_to_staff_id: UUID,
        task_type: str,
        title: str,
        due_date: datetime,
        description: str = None,
        priority: str = "medium",
        estimated_duration_minutes: int = 15,
        related_checkin_id: UUID = None,
        related_product_id: str = None,
        assigned_by_staff_id: UUID = None,
        db: Session = None
    ) -> dict:
        """Create and assign task to staff."""
        if not db:
            raise ValueError("Database session required")

        task = StaffTask(
            location_id=location_id,
            business_id=business_id,
            assigned_to_staff_id=assigned_to_staff_id,
            task_type=TaskType[task_type.upper()],
            title=title,
            description=description,
            due_date=due_date,
            priority=TaskPriority[priority.upper()],
            estimated_duration_minutes=estimated_duration_minutes,
            related_checkin_id=related_checkin_id,
            related_product_id=related_product_id,
            assigned_by_staff_id=assigned_by_staff_id,
        )

        db.add(task)
        db.commit()
        db.refresh(task)

        logger.info(f"Task assigned: {task.id} to staff {assigned_to_staff_id}")

        return {
            "task_id": str(task.id),
            "status": task.status.value,
            "title": task.title,
            "assigned_at": task.assigned_at.isoformat(),
            "due_date": task.due_date.isoformat()
        }

    @staticmethod
    def get_staff_tasks(
        staff_id: UUID,
        location_id: UUID = None,
        status_filter: str = None,
        db: Session = None
    ) -> list:
        """Get tasks assigned to staff."""
        if not db:
            raise ValueError("Database session required")

        query = db.query(StaffTask).filter(StaffTask.assigned_to_staff_id == staff_id)

        if location_id:
            query = query.filter(StaffTask.location_id == location_id)

        if status_filter:
            query = query.filter(StaffTask.status == TaskStatus[status_filter.upper()])

        # Check for overdue
        now = datetime.now(timezone.utc)
        tasks = query.order_by(StaffTask.due_date.asc()).all()

        for task in tasks:
            if task.status not in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]:
                if task.due_date < now:
                    task.status = TaskStatus.OVERDUE
                    db.commit()

        return tasks

    @staticmethod
    def acknowledge_task(
        task_id: UUID,
        db: Session
    ) -> dict:
        """Staff acknowledges task assignment."""
        task = db.query(StaffTask).filter(StaffTask.id == task_id).first()

        if not task:
            raise ValueError(f"Task {task_id} not found")

        task.status = TaskStatus.ACKNOWLEDGED
        task.acknowledged_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(task)

        logger.info(f"Task acknowledged: {task_id}")

        return {
            "task_id": str(task.id),
            "status": task.status.value,
            "acknowledged_at": task.acknowledged_at.isoformat()
        }

    @staticmethod
    def start_task(task_id: UUID, db: Session) -> dict:
        """Mark task as in-progress."""
        task = db.query(StaffTask).filter(StaffTask.id == task_id).first()

        if not task:
            raise ValueError(f"Task {task_id} not found")

        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(task)

        logger.info(f"Task started: {task_id}")

        return {
            "task_id": str(task.id),
            "status": task.status.value,
            "started_at": task.started_at.isoformat()
        }

    @staticmethod
    def complete_task(
        task_id: UUID,
        completion_notes: str = None,
        completion_evidence: dict = None,
        db: Session = None
    ) -> dict:
        """Mark task as completed."""
        if not db:
            raise ValueError("Database session required")

        task = db.query(StaffTask).filter(StaffTask.id == task_id).first()

        if not task:
            raise ValueError(f"Task {task_id} not found")

        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now(timezone.utc)
        task.completion_notes = completion_notes
        if completion_evidence:
            task.completion_evidence = completion_evidence

        db.commit()
        db.refresh(task)

        logger.info(f"Task completed: {task_id}")

        return {
            "task_id": str(task.id),
            "status": task.status.value,
            "completed_at": task.completed_at.isoformat(),
            "completion_time_minutes": _calculate_duration(task.started_at, task.completed_at)
        }

    @staticmethod
    def cancel_task(task_id: UUID, reason: str = None, db: Session = None) -> dict:
        """Cancel task."""
        if not db:
            raise ValueError("Database session required")

        task = db.query(StaffTask).filter(StaffTask.id == task_id).first()

        if not task:
            raise ValueError(f"Task {task_id} not found")

        task.status = TaskStatus.CANCELLED
        if reason:
            task.completion_notes = f"Cancelled: {reason}"

        db.commit()
        db.refresh(task)

        logger.info(f"Task cancelled: {task_id}")

        return {"task_id": str(task.id), "status": task.status.value}

    @staticmethod
    def get_task_queue(
        location_id: UUID,
        max_results: int = 10,
        db: Session = None
    ) -> dict:
        """Get pending tasks for location, ranked by priority + due date."""
        if not db:
            raise ValueError("Database session required")

        pending_statuses = [TaskStatus.ASSIGNED, TaskStatus.ACKNOWLEDGED, TaskStatus.IN_PROGRESS]
        now = datetime.now(timezone.utc)

        tasks = db.query(StaffTask).filter(
            StaffTask.location_id == location_id,
            StaffTask.status.in_(pending_statuses)
        ).order_by(
            StaffTask.priority.desc(),
            StaffTask.due_date.asc()
        ).limit(max_results).all()

        # Check for overdue
        for task in tasks:
            if task.due_date < now and task.status != TaskStatus.COMPLETED:
                task.status = TaskStatus.OVERDUE
                db.commit()

        task_list = [
            {
                "task_id": str(t.id),
                "title": t.title,
                "task_type": t.task_type.value,
                "assigned_to": str(t.assigned_to_staff_id),
                "priority": t.priority.value,
                "status": t.status.value,
                "due_date": t.due_date.isoformat(),
                "estimated_duration_minutes": t.estimated_duration_minutes,
                "time_until_due": (t.due_date - now).total_seconds() / 60  # minutes
            }
            for t in tasks
        ]

        return {
            "location_id": str(location_id),
            "pending_count": len(task_list),
            "tasks": task_list
        }

    @staticmethod
    def auto_assign_tasks_to_shift(
        location_id: UUID,
        staff_id: UUID,
        shift_start: datetime,
        db: Session = None
    ) -> dict:
        """Auto-assign queued tasks to staff starting shift."""
        if not db:
            raise ValueError("Database session required")

        # Get unassigned tasks for location
        unassigned = db.query(StaffTask).filter(
            StaffTask.location_id == location_id,
            StaffTask.status == TaskStatus.ASSIGNED,
            StaffTask.assigned_to_staff_id.is_(None)
        ).order_by(
            StaffTask.priority.desc(),
            StaffTask.due_date.asc()
        ).limit(5).all()

        assigned_count = 0
        for task in unassigned:
            task.assigned_to_staff_id = staff_id
            assigned_count += 1

        db.commit()

        logger.info(f"Auto-assigned {assigned_count} tasks to staff {staff_id}")

        return {
            "auto_assigned": assigned_count,
            "staff_id": str(staff_id),
            "shift_start": shift_start.isoformat()
        }


class TaskNotificationService:
    """Send + track task notifications."""

    @staticmethod
    def notify_task_assigned(
        task_id: UUID,
        staff_id: UUID,
        notification_channels: list = None,
        db: Session = None
    ) -> dict:
        """Send notification when task assigned to staff."""
        if not db:
            raise ValueError("Database session required")

        if not notification_channels:
            notification_channels = ["push", "in_app"]

        sent_count = 0
        for channel in notification_channels:
            notification = TaskNotification(
                task_id=task_id,
                staff_id=staff_id,
                notification_type=channel,
                delivery_status="sent"
            )
            db.add(notification)
            sent_count += 1

        db.commit()

        logger.info(f"Task notification sent: {task_id} via {sent_count} channels")

        return {
            "task_id": str(task_id),
            "notifications_sent": sent_count,
            "channels": notification_channels
        }

    @staticmethod
    def mark_notification_read(
        notification_id: UUID,
        db: Session
    ) -> dict:
        """Mark notification as read by staff."""
        notification = db.query(TaskNotification).filter(
            TaskNotification.id == notification_id
        ).first()

        if not notification:
            raise ValueError(f"Notification {notification_id} not found")

        notification.read_at = datetime.now(timezone.utc)
        db.commit()

        return {"notification_id": str(notification.id), "read_at": notification.read_at.isoformat()}


class ShiftReadinessService:
    """Generate shift readiness reports."""

    @staticmethod
    def generate_shift_report(
        location_id: UUID,
        business_id: UUID,
        staff_id: UUID,
        shift_start: datetime,
        shift_end: datetime = None,
        db: Session = None
    ) -> dict:
        """Generate task performance report for shift."""
        if not db:
            raise ValueError("Database session required")

        if not shift_end:
            shift_end = datetime.now(timezone.utc)

        # Get all tasks for this shift
        tasks = db.query(StaffTask).filter(
            StaffTask.location_id == location_id,
            StaffTask.assigned_to_staff_id == staff_id,
            StaffTask.assigned_at >= shift_start,
            StaffTask.assigned_at <= shift_end
        ).all()

        # Count by status
        completed = [t for t in tasks if t.status == TaskStatus.COMPLETED]
        acknowledged = [t for t in tasks if t.status == TaskStatus.ACKNOWLEDGED]
        overdue = [t for t in tasks if t.status == TaskStatus.OVERDUE]
        cancelled = [t for t in tasks if t.status == TaskStatus.CANCELLED]

        # Calculate metrics
        completion_rate = (len(completed) / len(tasks) * 100) if tasks else 0
        on_time = sum(1 for t in completed if t.completed_at <= t.due_date)

        avg_duration = None
        if completed:
            durations = [_calculate_duration(t.started_at, t.completed_at) for t in completed if t.started_at and t.completed_at]
            if durations:
                avg_duration = int(sum(durations) / len(durations))

        # Create report
        report = ShiftReadinessReport(
            location_id=location_id,
            business_id=business_id,
            staff_id=staff_id,
            shift_start=shift_start,
            shift_end=shift_end,
            total_tasks_assigned=len(tasks),
            tasks_completed=len(completed),
            tasks_acknowledged=len(acknowledged),
            tasks_overdue=len(overdue),
            tasks_cancelled=len(cancelled),
            completion_rate=int(completion_rate),
            avg_completion_time_minutes=avg_duration,
            tasks_completed_on_time=on_time
        )

        db.add(report)
        db.commit()
        db.refresh(report)

        logger.info(f"Shift report generated: {staff_id} completion_rate={int(completion_rate)}%")

        return {
            "report_id": str(report.id),
            "staff_id": str(staff_id),
            "shift_start": shift_start.isoformat(),
            "shift_end": shift_end.isoformat(),
            "total_tasks": len(tasks),
            "completed": len(completed),
            "completion_rate": int(completion_rate),
            "on_time": on_time,
            "overdue": len(overdue)
        }

    @staticmethod
    def get_staff_performance(
        staff_id: UUID,
        days: int = 30,
        db: Session = None
    ) -> dict:
        """Get staff task performance over time period."""
        if not db:
            raise ValueError("Database session required")

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        tasks = db.query(StaffTask).filter(
            StaffTask.assigned_to_staff_id == staff_id,
            StaffTask.assigned_at >= cutoff
        ).all()

        completed = [t for t in tasks if t.status == TaskStatus.COMPLETED]
        total = len(tasks)

        # Task types breakdown
        type_counts = {}
        for task in completed:
            task_type = task.task_type.value
            type_counts[task_type] = type_counts.get(task_type, 0) + 1

        completion_rate = (len(completed) / total * 100) if total else 0

        return {
            "staff_id": str(staff_id),
            "period_days": days,
            "total_tasks": total,
            "completed": len(completed),
            "completion_rate": int(completion_rate),
            "tasks_by_type": type_counts,
            "avg_priority": "medium"  # TODO: calculate
        }


def _calculate_duration(start: datetime, end: datetime) -> int:
    """Calculate duration in minutes."""
    if not start or not end:
        return 0
    return int((end - start).total_seconds() / 60)
