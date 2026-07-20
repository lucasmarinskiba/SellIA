"""Async Jobs — Celery for long-running tasks, background jobs, scheduling."""

import logging
import asyncio
from typing import Any, Dict, Optional, Callable, List, Coroutine
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class JobStatus(Enum):
    """Job status states."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class JobPriority(Enum):
    """Job priority levels."""
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    DEFERRED = 4


@dataclass
class Job:
    """Async job definition."""
    id: str
    name: str
    task: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    priority: JobPriority = JobPriority.NORMAL
    status: JobStatus = JobStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retries: int = 0
    max_retries: int = 3
    timeout_seconds: Optional[int] = None
    scheduled_for: Optional[datetime] = None

    def __post_init__(self):
        """Set defaults."""
        if not self.id:
            self.id = str(uuid.uuid4())

    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "priority": self.priority.name,
            "status": self.status.name,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "retries": self.retries,
            "execution_time_seconds": (
                (self.completed_at - self.started_at).total_seconds()
                if self.started_at and self.completed_at
                else None
            ),
        }


class AsyncJobQueue:
    """Async job queue manager (in-memory, production would use Celery + Redis)."""

    def __init__(self, worker_count: int = 4, max_queue_size: int = 10000):
        """Initialize job queue."""
        self.worker_count = worker_count
        self.max_queue_size = max_queue_size
        self.queue: List[Job] = []
        self.running_jobs: Dict[str, Job] = {}
        self.completed_jobs: Dict[str, Job] = {}
        self.failed_jobs: Dict[str, Job] = {}
        self.workers_active = False
        self.stats = {
            "total_jobs": 0,
            "completed": 0,
            "failed": 0,
            "avg_execution_time_ms": 0.0,
        }

    def enqueue(
        self,
        task: Callable,
        name: str,
        args: tuple = (),
        kwargs: Optional[Dict[str, Any]] = None,
        priority: JobPriority = JobPriority.NORMAL,
        timeout_seconds: Optional[int] = None,
        scheduled_for: Optional[datetime] = None,
    ) -> Job:
        """Enqueue a job."""

        if len(self.queue) >= self.max_queue_size:
            raise RuntimeError("Job queue is full")

        job = Job(
            id=str(uuid.uuid4()),
            name=name,
            task=task,
            args=args,
            kwargs=kwargs or {},
            priority=priority,
            timeout_seconds=timeout_seconds,
            scheduled_for=scheduled_for,
        )

        # Sort by priority (lower number = higher priority)
        self.queue.append(job)
        self.queue.sort(
            key=lambda j: (j.scheduled_for > datetime.utcnow() if j.scheduled_for else False, j.priority.value)
        )

        self.stats["total_jobs"] += 1
        logger.info(f"Job enqueued: {job.id} ({name}) with priority {priority.name}")

        return job

    async def execute_job(self, job: Job) -> None:
        """Execute a single job."""

        job.status = JobStatus.RUNNING
        job.started_at = datetime.utcnow()
        self.running_jobs[job.id] = job

        try:
            # Execute with timeout if specified
            if job.timeout_seconds:
                job.result = await asyncio.wait_for(
                    self._execute_task(job),
                    timeout=job.timeout_seconds
                )
            else:
                job.result = await self._execute_task(job)

            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            self.completed_jobs[job.id] = job
            self.stats["completed"] += 1

            logger.info(f"Job completed: {job.id} ({job.name})")

        except asyncio.TimeoutError:
            job.error = f"Job timed out after {job.timeout_seconds} seconds"
            job.status = JobStatus.FAILED
            self._handle_job_failure(job)

        except Exception as e:
            job.error = str(e)

            # Retry if under limit
            if job.retries < job.max_retries:
                job.retries += 1
                job.status = JobStatus.RETRYING
                self.queue.append(job)
                logger.warning(f"Job failed, retrying: {job.id} (attempt {job.retries})")
            else:
                job.status = JobStatus.FAILED
                self._handle_job_failure(job)
                logger.error(f"Job failed permanently: {job.id} - {e}")

        finally:
            self.running_jobs.pop(job.id, None)

    async def _execute_task(self, job: Job) -> Any:
        """Execute task as coroutine."""
        if asyncio.iscoroutinefunction(job.task):
            return await job.task(*job.args, **job.kwargs)
        else:
            # Run sync function in thread pool
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                job.task,
                *job.args,
            )

    def _handle_job_failure(self, job: Job) -> None:
        """Handle job failure."""
        self.failed_jobs[job.id] = job
        self.stats["failed"] += 1

    async def start_workers(self) -> None:
        """Start job workers."""
        if self.workers_active:
            return

        self.workers_active = True
        logger.info(f"Starting {self.worker_count} job workers")

        # Create worker tasks
        workers = [
            asyncio.create_task(self._worker_loop())
            for _ in range(self.worker_count)
        ]

        try:
            await asyncio.gather(*workers)
        except asyncio.CancelledError:
            logger.info("Job workers cancelled")

    async def stop_workers(self) -> None:
        """Stop job workers."""
        self.workers_active = False
        logger.info("Stopping job workers")

    async def _worker_loop(self) -> None:
        """Worker event loop."""
        while self.workers_active:
            # Find next job to execute
            job_to_run = None

            for i, job in enumerate(self.queue):
                # Check if job is scheduled for future
                if job.scheduled_for and job.scheduled_for > datetime.utcnow():
                    continue

                job_to_run = self.queue.pop(i)
                break

            if job_to_run:
                await self.execute_job(job_to_run)
            else:
                # No jobs available, wait a bit
                await asyncio.sleep(0.1)

    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job status."""
        # Check all job maps
        for jobs_dict in [self.running_jobs, self.completed_jobs, self.failed_jobs]:
            if job_id in jobs_dict:
                return jobs_dict[job_id].to_dict()

        return None

    def get_queue_status(self) -> Dict[str, Any]:
        """Get queue status."""
        return {
            "queue_size": len(self.queue),
            "running": len(self.running_jobs),
            "completed": len(self.completed_jobs),
            "failed": len(self.failed_jobs),
            "workers_active": self.workers_active,
            "worker_count": self.worker_count,
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        total = self.stats["completed"] + self.stats["failed"]
        success_rate = (
            self.stats["completed"] / total if total > 0 else 0
        )

        avg_execution_time = 0.0
        if self.completed_jobs:
            times = [
                (j.completed_at - j.started_at).total_seconds()
                for j in self.completed_jobs.values()
                if j.started_at and j.completed_at
            ]
            avg_execution_time = sum(times) / len(times) if times else 0.0

        return {
            "total_jobs_enqueued": self.stats["total_jobs"],
            "completed": self.stats["completed"],
            "failed": self.stats["failed"],
            "success_rate": round(success_rate, 3),
            "avg_execution_time_seconds": round(avg_execution_time, 2),
            "queue_size": len(self.queue),
            "running": len(self.running_jobs),
        }

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a pending job."""
        for i, job in enumerate(self.queue):
            if job.id == job_id:
                job.status = JobStatus.CANCELLED
                self.queue.pop(i)
                logger.info(f"Job cancelled: {job_id}")
                return True

        return False

    def clear_history(self, older_than_hours: int = 24) -> int:
        """Clear job history older than specified hours."""
        cutoff = datetime.utcnow() - timedelta(hours=older_than_hours)
        count = 0

        # Clear completed jobs
        keys_to_remove = [
            k for k, v in self.completed_jobs.items()
            if v.completed_at and v.completed_at < cutoff
        ]
        for k in keys_to_remove:
            del self.completed_jobs[k]
            count += 1

        # Clear failed jobs
        keys_to_remove = [
            k for k, v in self.failed_jobs.items()
            if v.completed_at and v.completed_at < cutoff
        ]
        for k in keys_to_remove:
            del self.failed_jobs[k]
            count += 1

        return count
