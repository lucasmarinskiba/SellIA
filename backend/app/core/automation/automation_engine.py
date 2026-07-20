"""
Automation Engine — Central brain that orchestrates 24/7 operations.

Sistema ejecuta estrategias SIN INTERVENCIÓN HUMANA.

Central orchestrator:
1. Task Scheduler: CUÁNDO hacer qué (hourly, daily, weekly, event-triggered)
2. Job Queue: QUÉ hacer (post product, respond inquiry, send email, etc)
3. State Manager: TRACKING estado cada tarea (pending → running → success/failed)
4. Retry Logic: si falla → reintentar con backoff inteligente
5. Escalation: si falla después retries → notificar humano
6. Monitoring: dashboard real-time de todas operaciones

Ejecuta 24/7 con ZERO intervención humana.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class JobType(Enum):
    """Tipos de jobs."""
    POST_PRODUCT = "post_product"
    RESPOND_INQUIRY = "respond_inquiry"
    SEND_EMAIL = "send_email"
    SYNC_INVENTORY = "sync_inventory"
    EXTRACT_ANALYTICS = "extract_analytics"
    PROCESS_PAYMENT = "process_payment"
    GENERATE_REPORT = "generate_report"
    TRACK_INFLUENCER = "track_influencer"
    RESPOND_REVIEW = "respond_review"
    UPDATE_PRICING = "update_pricing"


class JobStatus(Enum):
    """Estados de un job."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    ESCALATED = "escalated"
    SKIPPED = "skipped"
    ARCHIVED = "archived"


class Priority(Enum):
    """Niveles de prioridad."""
    CRITICAL = 100  # Immediate
    HIGH = 75  # Within minutes
    NORMAL = 50  # Within hours
    LOW = 25  # Background
    DEFERRED = 10  # Whenever


@dataclass
class Job:
    """Representa un job a ejecutar."""
    id: str
    job_type: JobType
    priority: Priority
    payload: Dict[str, Any]
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    attempts: int = 0
    max_retries: int = 3
    error: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    escalation_reason: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()

    @property
    def duration_seconds(self) -> float:
        """Duración total del job en segundos."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return 0.0

    @property
    def can_retry(self) -> bool:
        """¿Puede reintentar?"""
        return self.status == JobStatus.FAILED and self.attempts < self.max_retries


@dataclass
class Task:
    """Representa una tarea a agendar."""
    id: str
    name: str
    job_type: JobType
    priority: Priority
    schedule: str  # Cron expression o descripción
    payload: Dict[str, Any]
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


class AutomationEngine:
    """Central orchestrator. Ejecuta 24/7."""

    def __init__(
        self,
        scheduler,
        job_queue,
        state_manager,
        retry_handler,
        escalation_handler,
        monitoring,
    ):
        """
        Args:
            scheduler: TaskScheduler instance
            job_queue: JobQueue instance
            state_manager: StateManager instance
            retry_handler: RetryHandler instance
            escalation_handler: EscalationHandler instance
            monitoring: MonitoringDashboard instance
        """
        self.scheduler = scheduler
        self.job_queue = job_queue
        self.state_manager = state_manager
        self.retry_handler = retry_handler
        self.escalation_handler = escalation_handler
        self.monitoring = monitoring

        self.is_running = False
        self.cycle_count = 0
        self.registered_handlers: Dict[JobType, Callable] = {}

    def register_handler(self, job_type: JobType, handler: Callable) -> None:
        """Registra handler para tipo de job."""
        self.registered_handlers[job_type] = handler
        logger.info(f"Handler registered for {job_type.value}")

    async def run(self, cycle_limit: Optional[int] = None) -> None:
        """
        Main loop. Ejecuta 24/7.

        Args:
            cycle_limit: Para testing, limitar ciclos (None = infinito)
        """
        self.is_running = True
        logger.info("🚀 Automation Engine started")

        try:
            while self.is_running and (cycle_limit is None or self.cycle_count < cycle_limit):
                self.cycle_count += 1
                cycle_start = datetime.utcnow()

                try:
                    # 1. Obtener tasks del scheduler
                    tasks_to_run = await self.scheduler.get_tasks_for_now()
                    logger.debug(f"Cycle {self.cycle_count}: {len(tasks_to_run)} tasks ready")

                    # 2. Enqueue jobs
                    for task in tasks_to_run:
                        await self._enqueue_task(task)

                    # 3. Procesar jobs
                    await self._process_jobs()

                    # 4. Monitor health
                    cycle_duration = (datetime.utcnow() - cycle_start).total_seconds()
                    await self.monitoring.record_cycle(
                        self.cycle_count,
                        cycle_duration,
                        len(tasks_to_run),
                    )

                    # 5. Sleep until next cycle
                    await asyncio.sleep(1)

                except Exception as e:
                    logger.error(f"Cycle {self.cycle_count} error: {str(e)}", exc_info=True)
                    await self.monitoring.record_error("automation_cycle_error", str(e))

        except KeyboardInterrupt:
            logger.info("Automation Engine interrupted")
        finally:
            self.is_running = False
            logger.info("🛑 Automation Engine stopped")

    async def _enqueue_task(self, task: Task) -> None:
        """Convierte Task → Job → Queue."""
        try:
            job = Job(
                id=str(uuid.uuid4()),
                job_type=task.job_type,
                priority=task.priority,
                payload=task.payload,
            )

            await self.job_queue.enqueue(job)
            await self.state_manager.create(job)
            logger.debug(f"Job enqueued: {job.id} ({task.job_type.value})")

        except Exception as e:
            logger.error(f"Failed to enqueue task {task.id}: {str(e)}")

    async def _process_jobs(self) -> None:
        """Procesa jobs de la queue."""
        while not self.job_queue.empty():
            try:
                job = await self.job_queue.dequeue()
                if job is None:
                    break

                await self._execute_job(job)

            except Exception as e:
                logger.error(f"Job processing error: {str(e)}", exc_info=True)

    async def _execute_job(self, job: Job) -> None:
        """Ejecuta un job."""
        job.started_at = datetime.utcnow()
        job.status = JobStatus.RUNNING

        try:
            await self.state_manager.update(job.id, job)

            # Get handler for job type
            handler = self.registered_handlers.get(job.job_type)
            if not handler:
                raise ValueError(f"No handler for job type {job.job_type.value}")

            # Execute
            logger.info(f"Executing job {job.id} ({job.job_type.value})")
            job.result = await handler(job.payload)
            job.status = JobStatus.SUCCESS

            logger.info(f"Job succeeded: {job.id}")
            await self.monitoring.record_success(job)

        except Exception as e:
            logger.error(f"Job failed: {job.id}: {str(e)}", exc_info=True)
            job.error = str(e)
            job.attempts += 1

            # ¿Reintentar?
            if job.can_retry:
                job.status = JobStatus.FAILED
                await self.retry_handler.schedule_retry(job)
                logger.warning(f"Retry scheduled for job {job.id}")
            else:
                # Escalate
                job.status = JobStatus.ESCALATED
                job.escalation_reason = f"Max retries exceeded: {str(e)}"
                await self.escalation_handler.escalate(job)
                logger.warning(f"Job escalated: {job.id}")

            await self.monitoring.record_failure(job)

        finally:
            job.completed_at = datetime.utcnow()
            await self.state_manager.update(job.id, job)

    async def add_recurring_task(
        self,
        name: str,
        job_type: JobType,
        priority: Priority,
        schedule: str,
        payload: Dict[str, Any],
    ) -> str:
        """
        Agrega tarea recurrente.

        Args:
            name: Nombre descriptivo
            job_type: Tipo de job
            priority: Prioridad
            schedule: Cron expression ("0 9 * * *" = daily 9am)
            payload: Datos para el job

        Returns:
            Task ID
        """
        task = Task(
            id=str(uuid.uuid4()),
            name=name,
            job_type=job_type,
            priority=priority,
            schedule=schedule,
            payload=payload,
        )

        await self.scheduler.add_task(task)
        logger.info(f"Recurring task added: {name} ({schedule})")
        return task.id

    async def add_one_time_task(
        self,
        name: str,
        job_type: JobType,
        priority: Priority,
        payload: Dict[str, Any],
        run_at: datetime,
    ) -> str:
        """Agrega tarea de una sola ejecución."""
        task = Task(
            id=str(uuid.uuid4()),
            name=name,
            job_type=job_type,
            priority=priority,
            schedule="once",
            payload=payload,
            next_run=run_at,
        )

        await self.scheduler.add_task(task)
        logger.info(f"One-time task added: {name} (run_at: {run_at})")
        return task.id

    async def disable_task(self, task_id: str) -> None:
        """Deshabilita tarea."""
        await self.scheduler.disable_task(task_id)
        logger.info(f"Task disabled: {task_id}")

    async def enable_task(self, task_id: str) -> None:
        """Habilita tarea."""
        await self.scheduler.enable_task(task_id)
        logger.info(f"Task enabled: {task_id}")

    async def get_system_status(self) -> Dict[str, Any]:
        """Estado completo del sistema."""
        queued_jobs = self.job_queue.size()
        pending_jobs = await self.state_manager.count_by_status(JobStatus.PENDING)
        running_jobs = await self.state_manager.count_by_status(JobStatus.RUNNING)
        failed_jobs = await self.state_manager.count_by_status(JobStatus.FAILED)
        escalated_jobs = await self.state_manager.count_by_status(JobStatus.ESCALATED)

        return {
            "running": self.is_running,
            "cycle_count": self.cycle_count,
            "queue": {
                "size": queued_jobs,
                "pending": pending_jobs,
                "running": running_jobs,
            },
            "jobs": {
                "failed": failed_jobs,
                "escalated": escalated_jobs,
            },
            "metrics": await self.monitoring.get_metrics(),
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def graceful_shutdown(self) -> None:
        """Cierra gracefully."""
        logger.info("Gracefully shutting down...")
        self.is_running = False

        # Wait for current cycle to complete
        max_wait = 10
        waited = 0
        while waited < max_wait and self.job_queue.size() > 0:
            await asyncio.sleep(0.5)
            waited += 0.5

        if self.job_queue.size() > 0:
            logger.warning(f"Shutdown timeout: {self.job_queue.size()} jobs still queued")

        logger.info("Automation Engine shutdown complete")
