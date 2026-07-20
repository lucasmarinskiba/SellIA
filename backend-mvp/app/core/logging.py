"""Structured logging w/ JSON output for prod."""
import logging
import sys

from app.core.config import settings


def setup_logging() -> None:
    level = logging.DEBUG if settings.ENV == "dev" else logging.INFO

    fmt = (
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        if settings.ENV == "dev"
        else '{"ts":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","msg":"%(message)s"}'
    )

    logging.basicConfig(
        level=level,
        format=fmt,
        stream=sys.stdout,
    )
    # Silence noisy libs
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO if settings.ENV == "dev" else logging.WARNING)
