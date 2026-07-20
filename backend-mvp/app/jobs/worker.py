"""RQ worker entrypoint · run via `python -m app.jobs.worker`."""
from redis import Redis
from rq import Connection, Queue, Worker

from app.core.config import settings
from app.core.logging import setup_logging


def main() -> None:
    setup_logging()
    redis_conn = Redis.from_url(settings.REDIS_URL)
    with Connection(redis_conn):
        worker = Worker([Queue("default")])
        worker.work(with_scheduler=True)


if __name__ == "__main__":
    main()
