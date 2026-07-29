"""
Redis-based Email Scheduler
- Delayed sends (workflow step delays)
- Batch processing
- Retry queue
- Task persistence
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, List
from enum import Enum
import redis.asyncio as redis
import os

logger = logging.getLogger(__name__)

# ============================================================
# TASK ENUMS
# ============================================================
class TaskType(str, Enum):
    SEND_WORKFLOW_EMAIL = "send_workflow_email"
    SEND_BATCH_EMAILS = "send_batch_emails"
    UPDATE_LEAD_SCORE = "update_lead_score"
    PROGRESS_WORKFLOW = "progress_workflow"
    CHECK_NO_ENGAGEMENT = "check_no_engagement"

class TaskStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"

# ============================================================
# REDIS SCHEDULER
# ============================================================
class EmailScheduler:
    """Redis-based task scheduler for emails."""

    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or os.getenv(
            "REDIS_URL",
            "redis://localhost:6379/0"
        )
        self.redis: Optional[redis.Redis] = None
        self.queue_key = "sellia:queue"
        self.delayed_key = "sellia:delayed"
        self.failed_key = "sellia:failed"
        self.processing_key = "sellia:processing"

    async def connect(self) -> None:
        """Connect to Redis."""
        try:
            self.redis = await redis.from_url(self.redis_url, decode_responses=True)
            await self.redis.ping()
            logger.info("✅ Redis connected")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            logger.warning("Continuing without Redis (in-memory fallback)")
            self.redis = None

    async def close(self) -> None:
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()
            logger.info("✅ Redis connection closed")

    async def schedule_send_email(
        self,
        workflow_execution_id: int,
        lead_email: str,
        subject: str,
        body: str,
        send_at: Optional[datetime] = None,
        priority: int = 5
    ) -> str:
        """
        Queue email for sending.
        Priority: 1 (highest) to 10 (lowest)
        """
        task = {
            "type": TaskType.SEND_WORKFLOW_EMAIL,
            "workflow_execution_id": workflow_execution_id,
            "lead_email": lead_email,
            "subject": subject,
            "body": body,
            "send_at": (send_at or datetime.now()).isoformat(),
            "priority": priority,
            "attempts": 0,
            "created_at": datetime.now().isoformat(),
            "status": TaskStatus.QUEUED
        }

        task_id = f"task_{workflow_execution_id}_{datetime.now().timestamp()}"

        if not self.redis:
            logger.info(f"[MOCK] Queued: {task_id}")
            return task_id

        try:
            task_json = json.dumps(task)

            if send_at and send_at > datetime.now():
                # Delayed: store in sorted set with score=unix_timestamp
                score = send_at.timestamp()
                await self.redis.zadd(self.delayed_key, {task_id: score})
                logger.info(f"📅 Email scheduled for {send_at}: {task_id}")
            else:
                # Immediate: push to queue with priority
                await self.redis.lpush(self.queue_key, task_json)
                logger.info(f"📨 Email queued: {task_id}")

            return task_id

        except Exception as e:
            logger.error(f"Queue error: {e}")
            return task_id

    async def schedule_batch_emails(
        self,
        workflow_id: int,
        lead_emails: List[dict],  # [{ id, email, subject, body }, ...]
        send_at: Optional[datetime] = None
    ) -> str:
        """Queue batch of emails."""
        task = {
            "type": TaskType.SEND_BATCH_EMAILS,
            "workflow_id": workflow_id,
            "leads": lead_emails,
            "send_at": (send_at or datetime.now()).isoformat(),
            "count": len(lead_emails),
            "created_at": datetime.now().isoformat(),
            "status": TaskStatus.QUEUED
        }

        task_id = f"batch_{workflow_id}_{datetime.now().timestamp()}"

        if not self.redis:
            logger.info(f"[MOCK] Batch queued: {task_id} ({len(lead_emails)} emails)")
            return task_id

        try:
            task_json = json.dumps(task)

            if send_at and send_at > datetime.now():
                score = send_at.timestamp()
                await self.redis.zadd(self.delayed_key, {task_id: score})
            else:
                await self.redis.lpush(self.queue_key, task_json)

            logger.info(f"📨 Batch scheduled: {task_id} ({len(lead_emails)} emails)")
            return task_id

        except Exception as e:
            logger.error(f"Batch queue error: {e}")
            return task_id

    async def get_queue_stats(self) -> dict:
        """Get queue statistics."""
        if not self.redis:
            return {
                "queued": 0,
                "delayed": 0,
                "processing": 0,
                "failed": 0,
                "provider": "mock"
            }

        try:
            queued = await self.redis.llen(self.queue_key)
            delayed = await self.redis.zcard(self.delayed_key)
            processing = await self.redis.llen(self.processing_key)
            failed = await self.redis.llen(self.failed_key)

            return {
                "queued": queued,
                "delayed": delayed,
                "processing": processing,
                "failed": failed,
                "provider": "redis"
            }

        except Exception as e:
            logger.error(f"Stats error: {e}")
            return {"error": str(e)}

    async def move_delayed_to_queue(self) -> int:
        """Move expired delayed tasks to main queue."""
        if not self.redis:
            return 0

        try:
            now = datetime.now().timestamp()

            # Get all tasks ready to send
            tasks = await self.redis.zrangebyscore(
                self.delayed_key,
                0,
                now
            )

            if not tasks:
                return 0

            # Move to main queue
            for task_id in tasks:
                task_json = await self.redis.get(f"task:{task_id}")
                if task_json:
                    await self.redis.lpush(self.queue_key, task_json)
                await self.redis.zrem(self.delayed_key, task_id)

            logger.info(f"📨 Moved {len(tasks)} delayed tasks to queue")
            return len(tasks)

        except Exception as e:
            logger.error(f"Delayed move error: {e}")
            return 0

    async def peek_queue(self, count: int = 5) -> List[dict]:
        """Peek at queue without removing."""
        if not self.redis:
            return []

        try:
            tasks = await self.redis.lrange(self.queue_key, 0, count - 1)
            return [json.loads(t) for t in tasks if t]
        except Exception as e:
            logger.error(f"Peek error: {e}")
            return []

    async def pop_task(self) -> Optional[dict]:
        """Pop next task from queue."""
        if not self.redis:
            return None

        try:
            task_json = await self.redis.rpop(self.queue_key)
            if task_json:
                task = json.loads(task_json)
                # Move to processing
                await self.redis.lpush(self.processing_key, task_json)
                return task
            return None
        except Exception as e:
            logger.error(f"Pop error: {e}")
            return None

    async def mark_completed(self, task: dict) -> None:
        """Mark task as completed."""
        if not self.redis:
            return

        try:
            task_json = json.dumps(task)
            await self.redis.lrem(self.processing_key, 1, task_json)
            logger.info(f"✅ Task completed: {task.get('workflow_execution_id')}")
        except Exception as e:
            logger.error(f"Mark completed error: {e}")

    async def mark_failed(self, task: dict, error: str, retry: bool = True) -> None:
        """Mark task as failed, optionally retry."""
        if not self.redis:
            return

        try:
            task["attempts"] = task.get("attempts", 0) + 1
            task["error"] = error
            task["last_error_at"] = datetime.now().isoformat()

            task_json = json.dumps(task)

            if retry and task["attempts"] < 3:
                # Retry after 5 minutes
                retry_at = (datetime.now() + timedelta(minutes=5)).timestamp()
                await self.redis.zadd(self.delayed_key, {f"{task['workflow_execution_id']}:retry:{task['attempts']}": retry_at})
                logger.warning(f"⚠️ Task failed, retry #{task['attempts']}: {task['workflow_execution_id']}")
            else:
                # Move to failed
                await self.redis.lpush(self.failed_key, task_json)
                logger.error(f"❌ Task failed (no retry): {task['workflow_execution_id']}")

            await self.redis.lrem(self.processing_key, 1, task_json)

        except Exception as e:
            logger.error(f"Mark failed error: {e}")

# ============================================================
# FACTORY
# ============================================================
async def get_scheduler() -> EmailScheduler:
    """Factory to get configured scheduler."""
    scheduler = EmailScheduler()
    await scheduler.connect()
    return scheduler
