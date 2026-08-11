"""Background job queue system (Celery + Redis)."""

from dataclasses import dataclass
from typing import Optional, Any, Callable
from datetime import datetime, timedelta
from enum import Enum
import json
import uuid
import logging


logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class JobPriority(str, Enum):
    LOW = "low"  # Backups, analytics
    MEDIUM = "medium"  # Data syncs, reports
    HIGH = "high"  # Notifications, critical actions
    CRITICAL = "critical"  # Payment processing, security


@dataclass
class BackgroundJob:
    id: str
    job_type: str
    status: JobStatus
    priority: JobPriority
    payload: dict
    result: Optional[Any] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    next_retry_at: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


class BackgroundJobQueue:
    """
    Async job queue for long-running tasks.

    Supports:
    - Email sending
    - Data export (CSV/Excel)
    - Integration syncs (Salesforce, HubSpot)
    - Report generation
    - Webhook retries
    - Data analytics jobs
    - Machine learning model training
    """

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.jobs: dict[str, BackgroundJob] = {}
        self.handlers: dict[str, Callable] = {}
        self.retry_strategy = {
            JobPriority.CRITICAL: {"max_retries": 5, "backoff": 60},  # 1m base
            JobPriority.HIGH: {"max_retries": 3, "backoff": 30},  # 30s base
            JobPriority.MEDIUM: {"max_retries": 2, "backoff": 300},  # 5m base
            JobPriority.LOW: {"max_retries": 1, "backoff": 3600},  # 1h base
        }

    def enqueue(
        self,
        job_type: str,
        payload: dict,
        priority: JobPriority = JobPriority.MEDIUM,
        delay_seconds: int = 0,
    ) -> str:
        """
        Enqueue background job.

        Job types:
        - send_email: Email via SES
        - export_data: Generate CSV/Excel/PDF
        - sync_salesforce: Contact sync
        - sync_hubspot: Contact sync
        - generate_report: Analytics report
        - webhook_retry: Retry failed webhook
        - process_recording: Voice recording transcription
        - calculate_metrics: Expensive metric calculations
        """

        job_id = str(uuid.uuid4())
        job = BackgroundJob(
            id=job_id,
            job_type=job_type,
            status=JobStatus.PENDING,
            priority=priority,
            payload=payload,
            created_at=datetime.utcnow(),
        )

        if delay_seconds > 0:
            job.next_retry_at = datetime.utcnow() + timedelta(seconds=delay_seconds)

        self.jobs[job_id] = job
        logger.info(f"Enqueued job {job_id} ({job_type}, priority={priority})")
        return job_id

    def dequeue(self, priority: JobPriority = JobPriority.HIGH) -> Optional[BackgroundJob]:
        """
        Dequeue next pending job (highest priority first).
        """

        # Find pending jobs with matching priority
        pending = [
            j for j in self.jobs.values() if j.status == JobStatus.PENDING and j.priority == priority
        ]

        if pending:
            job = min(pending, key=lambda j: j.created_at)
            job.status = JobStatus.RUNNING
            job.started_at = datetime.utcnow()
            return job

        return None

    def execute(self, job: BackgroundJob) -> bool:
        """
        Execute job using registered handler.

        Returns: success (True/False)
        """

        handler = self.handlers.get(job.job_type)
        if not handler:
            error = f"No handler for job type: {job.job_type}"
            logger.error(error)
            self._mark_failed(job, error)
            return False

        try:
            logger.info(f"Executing job {job.id} ({job.job_type})")
            result = handler(job.payload)
            self._mark_completed(job, result)
            logger.info(f"Job {job.id} completed successfully")
            return True

        except Exception as e:
            logger.error(f"Job {job.id} failed: {str(e)}")
            self._handle_retry(job, str(e))
            return False

    def register_handler(self, job_type: str, handler: Callable) -> None:
        """
        Register handler function for job type.

        Handler signature: handler(payload: dict) -> result
        """

        self.handlers[job_type] = handler
        logger.info(f"Registered handler for job type: {job_type}")

    def _mark_completed(self, job: BackgroundJob, result: Any) -> None:
        """Mark job as completed."""

        job.status = JobStatus.COMPLETED
        job.result = result
        job.completed_at = datetime.utcnow()

    def _mark_failed(self, job: BackgroundJob, error: str) -> None:
        """Mark job as permanently failed."""

        job.status = JobStatus.FAILED
        job.error = error
        job.completed_at = datetime.utcnow()

    def _handle_retry(self, job: BackgroundJob, error: str) -> None:
        """
        Handle job failure with exponential backoff retry.

        Retry strategy:
        - CRITICAL: 5 retries, 60s base backoff (1m, 2m, 4m, 8m, 16m)
        - HIGH: 3 retries, 30s base backoff (30s, 1m, 2m)
        - MEDIUM: 2 retries, 5m base backoff (5m, 10m)
        - LOW: 1 retry, 1h base backoff (1h)
        """

        strategy = self.retry_strategy[job.priority]
        max_retries = strategy["max_retries"]
        base_backoff = strategy["backoff"]

        if job.retry_count < max_retries:
            job.retry_count += 1
            # Exponential backoff: base_backoff * (2 ^ retry_count)
            backoff_seconds = base_backoff * (2 ** (job.retry_count - 1))
            job.next_retry_at = datetime.utcnow() + timedelta(seconds=backoff_seconds)
            job.status = JobStatus.RETRYING
            logger.warning(
                f"Job {job.id} will retry ({job.retry_count}/{max_retries}) in {backoff_seconds}s"
            )
        else:
            self._mark_failed(job, f"Max retries exceeded: {error}")
            logger.error(f"Job {job.id} permanently failed after {max_retries} retries")

    def get_job_status(self, job_id: str) -> Optional[BackgroundJob]:
        """Get job status by ID."""

        return self.jobs.get(job_id)

    def list_jobs(self, status: Optional[JobStatus] = None, limit: int = 100) -> list[BackgroundJob]:
        """List jobs (optionally filtered by status)."""

        jobs = list(self.jobs.values())
        if status:
            jobs = [j for j in jobs if j.status == status]
        return sorted(jobs, key=lambda j: j.created_at, reverse=True)[:limit]

    def get_queue_stats(self) -> dict:
        """Get queue statistics."""

        all_jobs = list(self.jobs.values())
        return {
            "total_jobs": len(all_jobs),
            "pending": len([j for j in all_jobs if j.status == JobStatus.PENDING]),
            "running": len([j for j in all_jobs if j.status == JobStatus.RUNNING]),
            "completed": len([j for j in all_jobs if j.status == JobStatus.COMPLETED]),
            "failed": len([j for j in all_jobs if j.status == JobStatus.FAILED]),
            "retrying": len([j for j in all_jobs if j.status == JobStatus.RETRYING]),
            "avg_execution_time": self._get_avg_execution_time(all_jobs),
        }

    def _get_avg_execution_time(self, jobs: list[BackgroundJob]) -> float:
        """Calculate average execution time for completed jobs."""

        completed = [j for j in jobs if j.status == JobStatus.COMPLETED and j.started_at and j.completed_at]
        if not completed:
            return 0.0
        total_time = sum((j.completed_at - j.started_at).total_seconds() for j in completed)
        return total_time / len(completed)


# Singleton instance
job_queue = BackgroundJobQueue()


# ============================================================================
# JOB HANDLERS (Register these on startup)
# ============================================================================


def handle_send_email(payload: dict) -> dict:
    """Send email via SES."""

    to_email = payload.get("to_email")
    subject = payload.get("subject")
    body = payload.get("body")
    template = payload.get("template", "default")

    # TODO: Implement SES send
    logger.info(f"Sending email to {to_email}: {subject}")

    return {"email_id": str(uuid.uuid4()), "status": "sent"}


def handle_export_data(payload: dict) -> dict:
    """Generate data export (CSV/Excel/PDF)."""

    export_id = payload.get("export_id")
    entity_type = payload.get("entity_type")
    format = payload.get("format", "csv")
    filters = payload.get("filters", {})

    # TODO: Implement export logic
    logger.info(f"Exporting {entity_type} ({format}) with filters: {filters}")

    file_url = f"https://exports.sellia.app/{export_id}.{format}"
    return {"export_id": export_id, "file_url": file_url, "row_count": 0}


def handle_sync_salesforce(payload: dict) -> dict:
    """Sync contacts with Salesforce."""

    account_id = payload.get("account_id")
    sync_direction = payload.get("direction", "pull")  # pull or push

    # TODO: Implement Salesforce sync
    logger.info(f"Syncing Salesforce for account {account_id} ({sync_direction})")

    return {"account_id": account_id, "synced_count": 0, "status": "completed"}


def handle_process_recording(payload: dict) -> dict:
    """Process voice recording (transcription + sentiment)."""

    call_id = payload.get("call_id")
    recording_url = payload.get("recording_url")

    # TODO: Implement transcription (Twilio, AWS Transcribe, etc.)
    logger.info(f"Processing recording for call {call_id}")

    return {
        "call_id": call_id,
        "transcript": "[transcription here]",
        "sentiment": "positive",
        "duration_seconds": 0,
    }


def handle_webhook_retry(payload: dict) -> dict:
    """Retry failed webhook delivery."""

    webhook_id = payload.get("webhook_id")
    url = payload.get("url")
    event = payload.get("event")
    data = payload.get("data")

    # TODO: Implement webhook retry with validation
    logger.info(f"Retrying webhook {webhook_id} to {url}")

    return {"webhook_id": webhook_id, "status": "delivered"}


# Register all handlers on startup
def register_job_handlers():
    """Register all job handlers."""

    job_queue.register_handler("send_email", handle_send_email)
    job_queue.register_handler("export_data", handle_export_data)
    job_queue.register_handler("sync_salesforce", handle_sync_salesforce)
    job_queue.register_handler("sync_hubspot", handle_sync_salesforce)  # Similar handler
    job_queue.register_handler("process_recording", handle_process_recording)
    job_queue.register_handler("webhook_retry", handle_webhook_retry)

    logger.info("Background job handlers registered")
