"""Celery configuration for async background tasks."""

from celery import Celery
from celery.schedules import crontab
from celery.utils.log import get_task_logger
import os


# Celery app configuration
celery_app = Celery(
    "sellia",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1"),
)

celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Worker settings
    worker_prefetch_multiplier=1,  # Process 1 task at a time
    worker_max_tasks_per_child=1000,  # Restart worker every 1k tasks

    # Task timeout
    task_soft_time_limit=300,  # 5 minutes soft limit (exit gracefully)
    task_time_limit=600,  # 10 minutes hard limit (kill)

    # Result backend
    result_expires=3600,  # Results expire after 1 hour

    # Retry settings
    task_acks_late=True,  # Acknowledge after task completes
    task_reject_on_worker_lost=True,  # Requeue if worker dies

    # Schedule (beat scheduler)
    beat_schedule={
        # Sync integrations hourly
        "sync-salesforce-hourly": {
            "task": "backend.tasks.sync_salesforce_contacts",
            "schedule": crontab(minute=0),  # Every hour
            "options": {"queue": "integrations", "priority": 5},
        },
        "sync-hubspot-hourly": {
            "task": "backend.tasks.sync_hubspot_contacts",
            "schedule": crontab(minute=15),  # Every hour at :15
            "options": {"queue": "integrations", "priority": 5},
        },

        # Calculate forecasts daily at 1am UTC
        "calculate-forecasts-daily": {
            "task": "backend.tasks.calculate_revenue_forecasts",
            "schedule": crontab(hour=1, minute=0),
            "options": {"queue": "analytics", "priority": 3},
        },

        # Process voice recordings daily at 2am
        "process-recordings-daily": {
            "task": "backend.tasks.process_pending_recordings",
            "schedule": crontab(hour=2, minute=0),
            "options": {"queue": "processing", "priority": 3},
        },

        # Generate reports daily at 6am
        "generate-reports-daily": {
            "task": "backend.tasks.generate_scheduled_reports",
            "schedule": crontab(hour=6, minute=0),
            "options": {"queue": "reporting", "priority": 2},
        },

        # Clean up expired data daily at 3am
        "cleanup-expired-data": {
            "task": "backend.tasks.cleanup_expired_data",
            "schedule": crontab(hour=3, minute=0),
            "options": {"queue": "maintenance", "priority": 1},
        },

        # Retry failed webhooks every 5 minutes
        "retry-failed-webhooks": {
            "task": "backend.tasks.retry_failed_webhooks",
            "schedule": crontab(minute="*/5"),
            "options": {"queue": "webhooks", "priority": 6},
        },
    },

    # Task routing (different queues for different task types)
    task_routes={
        # Critical tasks (email, payments, approvals)
        "backend.tasks.send_email": {"queue": "critical"},
        "backend.tasks.process_payment": {"queue": "critical"},
        "backend.tasks.send_approval_notification": {"queue": "critical"},

        # High priority (integrations, webhooks)
        "backend.tasks.sync_*": {"queue": "integrations"},
        "backend.tasks.retry_*": {"queue": "webhooks"},

        # Medium priority (exports, reports, recording)
        "backend.tasks.export_*": {"queue": "processing"},
        "backend.tasks.generate_*": {"queue": "reporting"},
        "backend.tasks.process_recording": {"queue": "processing"},

        # Low priority (cleanup, maintenance)
        "backend.tasks.cleanup_*": {"queue": "maintenance"},
        "backend.tasks.calculate_*": {"queue": "analytics"},
    },
)


logger = get_task_logger(__name__)


# ============================================================================
# TASK DEFINITIONS
# ============================================================================


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_email(self, to_email: str, subject: str, body: str, template: str = "default"):
    """Send email via SES with retry."""
    try:
        logger.info(f"Sending email to {to_email}: {subject}")
        # TODO: Implement SES send
        return {"email_id": "email_001", "status": "sent"}
    except Exception as exc:
        logger.error(f"Email send failed: {exc}")
        # Exponential backoff: 60s, 120s, 240s
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@celery_app.task(bind=True, max_retries=2, default_retry_delay=300)
def export_deals_to_csv(self, user_id: str, filters: dict):
    """Generate CSV export (can be slow for large datasets)."""
    try:
        logger.info(f"Exporting deals for user {user_id} with filters: {filters}")
        # TODO: Generate CSV, upload to S3, send email
        return {"export_id": "export_001", "row_count": 1000}
    except Exception as exc:
        logger.error(f"Export failed: {exc}")
        raise self.retry(exc=exc, countdown=300 * (2 ** self.request.retries))


@celery_app.task(max_retries=3, default_retry_delay=30)
def sync_salesforce_contacts(account_id: str):
    """Sync contacts from Salesforce."""
    logger.info(f"Syncing Salesforce contacts for account {account_id}")
    # TODO: Implement Salesforce sync
    return {"synced_count": 50, "status": "completed"}


@celery_app.task(max_retries=3, default_retry_delay=30)
def sync_hubspot_contacts(account_id: str):
    """Sync contacts from HubSpot."""
    logger.info(f"Syncing HubSpot contacts for account {account_id}")
    # TODO: Implement HubSpot sync
    return {"synced_count": 45, "status": "completed"}


@celery_app.task(max_retries=2, default_retry_delay=120)
def process_voice_recording(call_id: str, recording_url: str):
    """Process voice recording (transcription + sentiment)."""
    logger.info(f"Processing recording for call {call_id}")
    # TODO: Transcribe via Twilio API or AWS Transcribe
    # TODO: Sentiment analysis
    return {
        "call_id": call_id,
        "transcript": "[transcription]",
        "sentiment": "positive",
    }


@celery_app.task(max_retries=1, default_retry_delay=3600)
def generate_scheduled_reports():
    """Generate and email all scheduled reports."""
    logger.info("Generating scheduled reports")
    # TODO: Query all active scheduled reports
    # TODO: Generate reports
    # TODO: Email users
    return {"generated_count": 25}


@celery_app.task(max_retries=1, default_retry_delay=300)
def calculate_revenue_forecasts():
    """Calculate revenue forecasts for all active deals."""
    logger.info("Calculating revenue forecasts")
    # TODO: Run forecast ML models
    # TODO: Update deal scores + probabilities
    return {"forecasted_deals": 500}


@celery_app.task(max_retries=1, default_retry_delay=300)
def process_pending_recordings():
    """Process all pending voice recordings."""
    logger.info("Processing pending recordings")
    # TODO: Find calls with recordings but no transcript
    # TODO: Process each recording
    return {"processed_count": 15}


@celery_app.task(max_retries=1, default_retry_delay=600)
def retry_failed_webhooks():
    """Retry webhooks that failed (exponential backoff)."""
    logger.info("Retrying failed webhooks")
    # TODO: Find failed webhooks
    # TODO: Retry with exponential backoff
    # TODO: Update status
    return {"retried_count": 5}


@celery_app.task(max_retries=1)
def cleanup_expired_data():
    """Clean up expired data (old exports, sessions, etc)."""
    logger.info("Cleaning up expired data")
    # TODO: Delete old exports (>30 days)
    # TODO: Delete expired sessions
    # TODO: Archive old records
    return {"cleaned_records": 1000}


# Health check task
@celery_app.task
def health_check():
    """Verify Celery + Redis working."""
    logger.info("Celery health check OK")
    return {"status": "healthy"}


# ============================================================================
# WORKER COMMANDS
# ============================================================================

"""
Start workers:

# All tasks (development)
celery -A backend.celery_app worker --loglevel=info --concurrency=4

# Critical queue only (high priority)
celery -A backend.celery_app worker -Q critical --loglevel=info --concurrency=2

# Integration queue (medium priority)
celery -A backend.celery_app worker -Q integrations --loglevel=info --concurrency=2

# Processing queue (medium priority)
celery -A backend.celery_app worker -Q processing --loglevel=info --concurrency=1

# Multiple queues with priority
celery -A backend.celery_app worker -Q critical,webhooks,integrations,reporting,processing,maintenance --loglevel=info --concurrency=4

Start scheduler (beat):
celery -A backend.celery_app beat --loglevel=info

Start monitoring (flower):
celery -A backend.celery_app flower --port=5555
"""
