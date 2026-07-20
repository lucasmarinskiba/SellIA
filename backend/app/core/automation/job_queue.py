"""
Job Queue — QUÉ hacer y en qué orden.

Características:
- Priority queue (urgent first)
- Max concurrent jobs per platform (avoid rate limits)
- Dead letter queue (permanently failed jobs)
- Job deduplication (don't post same product 2×)
- Job batching (group similar tasks)
- Fair processing (FIFO + priority hybrid)

Priority levels:
- 100: Inquiry response (urgent)
- 75: Product post (important)
- 50: Email campaign (normal)
- 30: Report generation (background)
- 10: Analytics (lowest)
"""

import logging
import asyncio
from typing import Optional, Dict, List, Any
from heapq import heappush, heappop
from collections import defaultdict
from datetime import datetime

logger = logging.getLogger(__name__)


class JobQueue:
    """Priority queue con deduplication y rate limiting."""

    def __init__(self, max_concurrent_per_platform: int = 3):
        self.queue: List[tuple] = []  # Min heap: (priority, sequence, job)
        self.sequence = 0  # Tie-breaker para FIFO en misma prioridad
        self.seen_jobs: set = set()  # Para deduplicación
        self.dead_letter_queue: List[Any] = []
        self.active_jobs: Dict[str, Any] = {}  # job_id → Job
        self.platform_active_count: Dict[str, int] = defaultdict(int)
        self.max_concurrent_per_platform = max_concurrent_per_platform
        self.lock = asyncio.Lock()

    async def enqueue(self, job: Any) -> bool:
        """
        Agrega job a la queue.

        Returns:
            True si se enqueó, False si fue deduplicado
        """
        async with self.lock:
            # Check deduplication
            job_hash = self._hash_job(job)
            if job_hash in self.seen_jobs:
                logger.debug(f"Job deduplicated: {job.id}")
                return False

            # Add to heap
            self.sequence += 1
            priority_score = -job.priority.value  # Negative para max heap
            heappush(self.queue, (priority_score, self.sequence, job))

            self.seen_jobs.add(job_hash)
            logger.debug(f"Job enqueued: {job.id} (priority: {job.priority.value})")
            return True

    async def dequeue(self) -> Optional[Any]:
        """Obtiene próximo job respetando rate limits."""
        async with self.lock:
            while self.queue:
                # Check rate limits for platform
                priority_score, sequence, job = heappop(self.queue)

                # Extract platform from payload
                platform = job.payload.get("platform", "default")

                # Check if we can process this platform
                if self.platform_active_count[platform] >= self.max_concurrent_per_platform:
                    logger.debug(
                        f"Rate limit reached for {platform}. "
                        f"Job {job.id} re-queued."
                    )
                    # Re-add to queue
                    heappush(self.queue, (priority_score, sequence, job))
                    return None

                # Mark as active
                self.active_jobs[job.id] = job
                self.platform_active_count[platform] += 1
                logger.debug(f"Job dequeued: {job.id} ({platform})")

                return job

            return None

    async def mark_completed(self, job_id: str) -> None:
        """Marca job como completado."""
        async with self.lock:
            if job_id in self.active_jobs:
                job = self.active_jobs.pop(job_id)
                platform = job.payload.get("platform", "default")
                self.platform_active_count[platform] -= 1
                logger.debug(f"Job completed: {job_id}")

    async def mark_dead_letter(self, job: Any, reason: str) -> None:
        """Mueve job a dead letter queue (sin salida)."""
        async with self.lock:
            self.dead_letter_queue.append({
                "job_id": job.id,
                "job_type": job.job_type.value,
                "reason": reason,
                "timestamp": datetime.utcnow().isoformat(),
                "payload": job.payload,
            })
            logger.warning(f"Job moved to DLQ: {job.id} ({reason})")

    def size(self) -> int:
        """Cantidad de jobs en queue."""
        return len(self.queue)

    async def get_stats(self) -> Dict[str, Any]:
        """Estadísticas de la queue."""
        async with self.lock:
            return {
                "queued": len(self.queue),
                "active": len(self.active_jobs),
                "dead_letter": len(self.dead_letter_queue),
                "platform_active_count": dict(self.platform_active_count),
            }

    async def get_dead_letters(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Obtiene jobs del dead letter queue."""
        async with self.lock:
            return self.dead_letter_queue[-limit:]

    def _hash_job(self, job: Any) -> str:
        """Genera hash de job para deduplicación."""
        # Simple deduplication basada en job_type + payload key fields
        key_fields = [
            job.job_type.value,
            job.payload.get("product_id"),
            job.payload.get("customer_id"),
            job.payload.get("platform"),
        ]
        return "|".join(str(f) for f in key_fields if f is not None)

    async def clear_dead_letters_older_than(self, hours: int = 24) -> int:
        """Limpia DLQ old entries."""
        async with self.lock:
            cutoff_time = datetime.utcnow().timestamp() - (hours * 3600)
            original_count = len(self.dead_letter_queue)

            self.dead_letter_queue = [
                dlq for dlq in self.dead_letter_queue
                if datetime.fromisoformat(dlq["timestamp"]).timestamp() > cutoff_time
            ]

            removed = original_count - len(self.dead_letter_queue)
            logger.info(f"DLQ cleaned: {removed} entries removed")
            return removed


class BatchJobQueue(JobQueue):
    """Job queue con soporte para batch processing."""

    def __init__(self, max_concurrent_per_platform: int = 3):
        super().__init__(max_concurrent_per_platform)
        self.batch_groups: Dict[str, List[Any]] = {}  # batch_key → List[Job]
        self.batch_config: Dict[str, Dict[str, int]] = {
            "email": {"max_batch": 10, "timeout_seconds": 30},
            "post_product": {"max_batch": 5, "timeout_seconds": 60},
            "sync_inventory": {"max_batch": 20, "timeout_seconds": 45},
        }

    async def enqueue_batch(self, jobs: List[Any], batch_key: str) -> int:
        """
        Agrupa jobs similares para procesamiento batch.

        Returns:
            Cantidad de jobs enqueados
        """
        async with self.lock:
            if batch_key not in self.batch_groups:
                self.batch_groups[batch_key] = []

            added = 0
            for job in jobs:
                job_hash = self._hash_job(job)
                if job_hash not in self.seen_jobs:
                    self.batch_groups[batch_key].append(job)
                    self.seen_jobs.add(job_hash)
                    added += 1

            # If batch is full or timeout, enqueue as batch
            batch_config = self.batch_config.get(batch_key, {})
            max_batch = batch_config.get("max_batch", 10)

            if len(self.batch_groups[batch_key]) >= max_batch:
                await self._enqueue_batch_group(batch_key)

            logger.debug(f"Batch {batch_key}: {added} jobs added")
            return added

    async def _enqueue_batch_group(self, batch_key: str) -> None:
        """Enqueue a batch group como un job único."""
        jobs = self.batch_groups.pop(batch_key, [])
        if not jobs:
            return

        # Create batch job
        batch_job = self._create_batch_job(batch_key, jobs)
        self.sequence += 1
        priority_score = -batch_job.priority.value

        heappush(self.queue, (priority_score, self.sequence, batch_job))
        logger.info(f"Batch enqueued: {batch_key} with {len(jobs)} jobs")

    @staticmethod
    def _create_batch_job(batch_key: str, jobs: List[Any]) -> Any:
        """Crea un job batch a partir de múltiples jobs."""
        from automation_engine import Job, Priority, JobType, JobStatus
        import uuid

        batch_job = Job(
            id=str(uuid.uuid4()),
            job_type=JobType[batch_key.upper()] if batch_key.upper() in JobType.__members__ else JobType.POST_PRODUCT,
            priority=Priority.NORMAL,
            payload={
                "batch_key": batch_key,
                "jobs": [job.payload for job in jobs],
                "count": len(jobs),
            },
            status=JobStatus.PENDING,
        )
        return batch_job

    async def flush_batches(self) -> Dict[str, int]:
        """Enqueue todas los batch groups pendientes."""
        async with self.lock:
            flushed = {}
            for batch_key in list(self.batch_groups.keys()):
                if self.batch_groups[batch_key]:
                    count = len(self.batch_groups[batch_key])
                    await self._enqueue_batch_group(batch_key)
                    flushed[batch_key] = count

            logger.info(f"Batches flushed: {flushed}")
            return flushed
