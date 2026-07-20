"""
Retry Handler — Schedule retries con exponential backoff.

Se integra con RetryEngine del proyecto para:
- Exponential backoff: 1s → 2s → 4s → 8s → 16s → 30s (max)
- Max 3 retries por defecto (configurable por policy)
- Aplicable a: pagos fallidos, webhook fails, API timeouts
- Circuit breaker: stop retrying si service está down
"""

import logging
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class RetryPolicy(Enum):
    """Políticas de retry."""
    AGGRESSIVE = "aggressive"  # 5 retries, fast backoff
    DEFAULT = "default"  # 3 retries, normal backoff
    CONSERVATIVE = "conservative"  # 1 retry, long waits
    PAYMENT = "payment"  # 3 retries, long waits


class RetryHandler:
    """Gestiona retries de jobs."""

    def __init__(self, job_queue, state_manager):
        self.job_queue = job_queue
        self.state_manager = state_manager
        self.retry_queue: Dict[str, Dict[str, Any]] = {}
        self.lock = asyncio.Lock()

    async def schedule_retry(
        self,
        job: Any,
        policy: RetryPolicy = RetryPolicy.DEFAULT,
    ) -> None:
        """
        Agenda retry de un job.

        Args:
            job: Job a reintentar
            policy: Política de retry
        """
        async with self.lock:
            delay = self._calculate_delay(job.attempts, policy)
            retry_at = datetime.utcnow() + timedelta(seconds=delay)

            self.retry_queue[job.id] = {
                "job": job,
                "retry_at": retry_at,
                "policy": policy,
                "delay_seconds": delay,
            }

            logger.info(
                f"Retry scheduled for {job.id}: attempt {job.attempts + 1} "
                f"in {delay:.1f}s"
            )

    async def process_retries(self) -> int:
        """
        Procesa retries que están listos.

        Returns:
            Cantidad de retries procesados
        """
        now = datetime.utcnow()
        retries_ready = []

        async with self.lock:
            for job_id, retry_info in list(self.retry_queue.items()):
                if retry_info["retry_at"] <= now:
                    retries_ready.append(retry_info)
                    del self.retry_queue[job_id]

        # Enqueue ready retries
        for retry_info in retries_ready:
            job = retry_info["job"]
            await self.job_queue.enqueue(job)
            logger.info(f"Retry enqueued: {job.id} (attempt {job.attempts + 1})")

        return len(retries_ready)

    async def get_pending_retries(self) -> Dict[str, Dict[str, Any]]:
        """Obtiene retries pendientes."""
        async with self.lock:
            return dict(self.retry_queue)

    @staticmethod
    def _calculate_delay(
        attempt_number: int,
        policy: RetryPolicy,
    ) -> float:
        """Calcula delay con exponential backoff."""
        policy_config = {
            RetryPolicy.AGGRESSIVE: {
                "base": 0.5,
                "multiplier": 1.5,
                "max": 15,
            },
            RetryPolicy.DEFAULT: {
                "base": 1.0,
                "multiplier": 2.0,
                "max": 30,
            },
            RetryPolicy.CONSERVATIVE: {
                "base": 5.0,
                "multiplier": 2.0,
                "max": 60,
            },
            RetryPolicy.PAYMENT: {
                "base": 2.0,
                "multiplier": 2.5,
                "max": 120,
            },
        }

        config = policy_config.get(policy, policy_config[RetryPolicy.DEFAULT])
        delay = config["base"] * (config["multiplier"] ** attempt_number)
        delay = min(delay, config["max"])

        # Add jitter (±10%)
        import random
        jitter = random.uniform(0.9, 1.1)
        return delay * jitter

    async def cancel_retry(self, job_id: str) -> bool:
        """Cancela retry pendiente."""
        async with self.lock:
            if job_id in self.retry_queue:
                del self.retry_queue[job_id]
                logger.info(f"Retry cancelled: {job_id}")
                return True
        return False
