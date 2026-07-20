"""RQ queue · sync helper to enqueue from async code."""
from typing import Any, Callable

from redis import Redis
from rq import Queue

from app.core.config import settings


_redis: Redis | None = None
_queue: Queue | None = None


def get_queue() -> Queue:
    global _redis, _queue
    if _queue is None:
        _redis = Redis.from_url(settings.REDIS_URL)
        _queue = Queue("default", connection=_redis, default_timeout=600)
    return _queue


def enqueue(func: Callable[..., Any], *args, **kwargs):
    """Enqueue job · returns job id."""
    return get_queue().enqueue(func, *args, **kwargs)
