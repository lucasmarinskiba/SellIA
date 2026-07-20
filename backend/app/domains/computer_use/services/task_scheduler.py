"""Task Scheduler & Conflict Resolution.

Encola tareas, evita conflictos, prioriza, ejecuta en orden.
Soporta: responder mensajes, agendar, cerrar ventas, lanzar ads.
"""

import logging
from typing import Dict, List, Any, Optional, Callable, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from heapq import heappush, heappop

logger = logging.getLogger(__name__)


class TaskType(str, Enum):
    """Tipos de tareas."""
    RESPOND_MESSAGE = "respond_message"
    SCHEDULE_APPOINTMENT = "schedule_appointment"
    CLOSE_SALE = "close_sale"
    LAUNCH_AD_CAMPAIGN = "launch_ad_campaign"
    SEND_FOLLOW_UP = "send_follow_up"
    NURTURE_LEAD = "nurture_lead"
    RE_ENGAGEMENT = "re_engagement"
    HANDLE_OBJECTION = "handle_objection"


class TaskPriority(int, Enum):
    """Prioridades (lower = ejecuta primero)."""
    URGENT = 1  # Responder customer
    HIGH = 2  # Cerrar venta
    MEDIUM = 3  # Seguimiento
    LOW = 4  # Nurture
    BATCH = 5  # Tareas batch


@dataclass
class Task:
    """Tarea a ejecutar."""

    task_id: str
    task_type: TaskType
    priority: TaskPriority
    user_id: str
    customer_id: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)  # Datos específicos de tarea
    due_at: datetime = None  # Cuándo ejecutar
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = field(default_factory=datetime.utcnow)
    status: str = "pending"  # pending, running, completed, failed, conflict

    # Para heap queue (comparación)
    def __lt__(self, other):
        # Primero por priority, luego por due_at, luego por created_at
        if self.priority != other.priority:
            return self.priority < other.priority
        if self.due_at != other.due_at:
            return self.due_at < other.due_at
        return self.created_at < other.created_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task_type": self.task_type.value,
            "priority": self.priority.name,
            "status": self.status,
            "due_at": self.due_at.isoformat() if self.due_at else None,
            "created_at": self.created_at.isoformat(),
            "retry_count": self.retry_count,
        }


class ConflictCheck:
    """Resultado de validación de conflictos."""

    def __init__(self, has_conflict: bool, reason: str = ""):
        self.has_conflict = has_conflict
        self.reason = reason
        self.resolution: Optional[str] = None  # cómo resolverlo
        self.alternative_time: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "has_conflict": self.has_conflict,
            "reason": self.reason,
            "resolution": self.resolution,
            "alternative_time": self.alternative_time.isoformat() if self.alternative_time else None,
        }


class TaskScheduler:
    """Orchestrador de tareas."""

    # Límites por tipo de tarea
    MAX_CONCURRENT_TASKS = 10
    MAX_TASKS_PER_CUSTOMER_PER_HOUR = 5

    # Conflictos conocidos
    CONFLICTING_TASK_PAIRS = [
        (TaskType.RESPOND_MESSAGE, TaskType.CLOSE_SALE),  # Responder y cerrar simultáneamente no tiene sentido
        (TaskType.SCHEDULE_APPOINTMENT, TaskType.LAUNCH_AD_CAMPAIGN),  # No en mismo momento
    ]

    def __init__(self):
        self.logger = logger
        self.task_queue: List[Task] = []  # Priority queue
        self.executing_tasks: Dict[str, Task] = {}  # task_id → Task (running)
        self.customer_task_history: Dict[str, List[Task]] = {}  # customer_id → tasks
        self.completed_tasks: List[Task] = []

    async def enqueue_task(
        self,
        task_type: TaskType,
        user_id: str,
        payload: Dict[str, Any],
        priority: Optional[TaskPriority] = None,
        customer_id: Optional[str] = None,
        due_at: Optional[datetime] = None,
    ) -> Tuple[str, bool, Optional[str]]:
        """
        Encola tarea con validación de conflictos.

        Retorna: (task_id, success, conflict_reason)
        """
        # Asignar prioridad por defecto
        if not priority:
            priority = self._default_priority(task_type)

        # Usar ahora si no hay due_at
        if not due_at:
            due_at = datetime.utcnow()

        task_id = f"task_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{task_type.value}"

        task = Task(
            task_id=task_id,
            task_type=task_type,
            priority=priority,
            user_id=user_id,
            customer_id=customer_id,
            payload=payload,
            due_at=due_at,
        )

        # Validar conflictos
        conflict = await self._check_conflicts(task)

        if conflict.has_conflict:
            # Intentar reschedule
            if conflict.alternative_time:
                task.due_at = conflict.alternative_time
                self.logger.info(f"Task rescheduled: {task_id} | reason={conflict.reason}")
            else:
                task.status = "conflict"
                self.logger.warning(f"Task conflict (not resolvable): {task_id} | reason={conflict.reason}")
                return task_id, False, conflict.reason

        # Encolar
        heappush(self.task_queue, task)

        # Registrar en historial
        if customer_id:
            if customer_id not in self.customer_task_history:
                self.customer_task_history[customer_id] = []
            self.customer_task_history[customer_id].append(task)

        self.logger.info(f"Task enqueued: {task_id} | type={task_type.value} | priority={priority.name}")

        return task_id, True, None

    async def execute_next(self) -> Optional[Task]:
        """Ejecuta siguiente tarea en queue."""
        if not self.task_queue:
            return None

        # Obtener siguiente tarea
        task = heappop(self.task_queue)

        # Validar que no haya tarea ejecutándose en paralelo
        if len(self.executing_tasks) >= self.MAX_CONCURRENT_TASKS:
            # Re-encolar
            heappush(self.task_queue, task)
            self.logger.warning("Task queue full, re-queuing task")
            return None

        task.status = "running"
        self.executing_tasks[task.task_id] = task

        self.logger.info(f"Executing task: {task.task_id} | type={task.task_type.value}")

        return task

    async def mark_completed(self, task_id: str, result: Any = None) -> bool:
        """Marca tarea como completada."""
        task = self.executing_tasks.pop(task_id, None)

        if not task:
            self.logger.warning(f"Task not found in executing: {task_id}")
            return False

        task.status = "completed"
        self.completed_tasks.append(task)

        self.logger.info(f"Task completed: {task_id}")

        return True

    async def mark_failed(self, task_id: str, error: str = "") -> bool:
        """Marca tarea como fallida (con reintentos)."""
        task = self.executing_tasks.pop(task_id, None)

        if not task:
            return False

        task.retry_count += 1

        if task.retry_count <= task.max_retries:
            # Re-encolar con backoff
            task.status = "pending"
            task.due_at = datetime.utcnow() + timedelta(seconds=2 ** task.retry_count)
            heappush(self.task_queue, task)

            self.logger.warning(
                f"Task failed (will retry): {task_id} | retry={task.retry_count}/{task.max_retries} | error={error}"
            )
            return True
        else:
            # Max retries alcanzado
            task.status = "failed"
            self.completed_tasks.append(task)

            self.logger.error(f"Task permanently failed: {task_id} | error={error}")
            return False

    async def get_queue_status(self) -> Dict[str, Any]:
        """Retorna status actual de la queue."""
        pending_by_priority = {}
        for task in self.task_queue:
            priority = task.priority.name
            if priority not in pending_by_priority:
                pending_by_priority[priority] = 0
            pending_by_priority[priority] += 1

        return {
            "pending_count": len(self.task_queue),
            "pending_by_priority": pending_by_priority,
            "executing_count": len(self.executing_tasks),
            "completed_count": len(self.completed_tasks),
            "total_capacity": self.MAX_CONCURRENT_TASKS,
        }

    # ── Private Methods ──────────────────────────────────────────

    def _default_priority(self, task_type: TaskType) -> TaskPriority:
        """Asigna prioridad por defecto según tipo de tarea."""
        if task_type in (TaskType.RESPOND_MESSAGE, TaskType.HANDLE_OBJECTION):
            return TaskPriority.URGENT
        elif task_type in (TaskType.CLOSE_SALE, TaskType.SCHEDULE_APPOINTMENT):
            return TaskPriority.HIGH
        elif task_type == TaskType.SEND_FOLLOW_UP:
            return TaskPriority.MEDIUM
        elif task_type == TaskType.LAUNCH_AD_CAMPAIGN:
            return TaskPriority.MEDIUM
        else:
            return TaskPriority.LOW

    async def _check_conflicts(self, task: Task) -> ConflictCheck:
        """Valida si tarea va en conflicto con otras."""
        # Conflicto 1: Demasiadas tareas por customer en poco tiempo
        if task.customer_id:
            customer_tasks = self.customer_task_history.get(task.customer_id, [])
            recent_tasks = [
                t
                for t in customer_tasks
                if (datetime.utcnow() - t.created_at).total_seconds() < 3600  # Última hora
            ]

            if len(recent_tasks) >= self.MAX_TASKS_PER_CUSTOMER_PER_HOUR:
                # Sugerir ejecutar después de 1 hora
                alt_time = datetime.utcnow() + timedelta(hours=1)
                return ConflictCheck(
                    has_conflict=True,
                    reason=f"Too many tasks for this customer in past hour ({len(recent_tasks)}/{self.MAX_TASKS_PER_CUSTOMER_PER_HOUR})",
                )

        # Conflicto 2: Tareas que no deben ejecutarse en paralelo
        for task_type_a, task_type_b in self.CONFLICTING_TASK_PAIRS:
            if task.task_type == task_type_a:
                # Verificar si hay tarea_b ejecutándose
                for exec_task in self.executing_tasks.values():
                    if exec_task.task_type == task_type_b and exec_task.customer_id == task.customer_id:
                        return ConflictCheck(
                            has_conflict=True,
                            reason=f"Conflict: cannot execute {task.task_type.value} while {task_type_b.value} is running",
                        )

        # Sin conflictos
        return ConflictCheck(has_conflict=False)


def get_task_scheduler() -> TaskScheduler:
    return TaskScheduler()
