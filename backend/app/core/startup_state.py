"""Liveness vs. readiness for the background database bootstrap.

The lifespan used to run every schema bootstrap to completion *before* yielding,
and uvicorn does not bind its port until the lifespan yields. On Railway that
meant ~13 minutes of 502 "Application failed to respond" on every deploy or
restart, /api/health included.

The bootstrap now runs as a background task after the lifespan yields, so the
process is *alive* within seconds. This module records how far that task got so
the two questions can be answered separately:

* ``/api/health`` and ``/health`` -- liveness: the process is up and serving.
  Cheap, never waits on the bootstrap. This is what Railway's healthcheck hits.
* ``/api/ready`` -- readiness: the bootstrap finished, so every table and column
  the code expects exists. 503 (with Retry-After) until then. CI jobs that talk
  to a *fresh* database (E2E, seed scripts) must wait on this, not on liveness.
"""

from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

PENDING = "pending"
RUNNING = "running"
COMPLETE = "complete"
FAILED = "failed"


class StartupState:
    """Progress of the background bootstrap; one instance per process."""

    def __init__(self) -> None:
        self.phase: str = PENDING
        self.error: str | None = None
        self._started_at: float | None = None
        self._finished_at: float | None = None
        self._steps: dict[str, float] = {}

    def start(self) -> None:
        self.phase = RUNNING
        self.error = None
        self._started_at = time.monotonic()
        self._finished_at = None
        self._steps = {}

    def mark(self, step: str) -> None:
        """Record that ``step`` finished, as seconds since the bootstrap started."""
        if self._started_at is not None:
            self._steps[step] = round(time.monotonic() - self._started_at, 2)

    def complete(self) -> None:
        self.phase = COMPLETE
        self._finished_at = time.monotonic()

    def fail(self, exc: BaseException) -> None:
        self.phase = FAILED
        self.error = f"{type(exc).__name__}: {str(exc)[:200]}"
        self._finished_at = time.monotonic()

    @property
    def ready(self) -> bool:
        return self.phase == COMPLETE

    @property
    def done(self) -> bool:
        """True once the bootstrap stopped running, successfully or not."""
        return self.phase in (COMPLETE, FAILED)

    @property
    def elapsed_seconds(self) -> float | None:
        if self._started_at is None:
            return None
        end = self._finished_at if self._finished_at is not None else time.monotonic()
        return round(end - self._started_at, 2)

    def snapshot(self) -> dict[str, Any]:
        return {
            "ready": self.ready,
            "phase": self.phase,
            "elapsed_seconds": self.elapsed_seconds,
            "steps": dict(self._steps),
            "error": self.error,
        }


startup_state = StartupState()

router = APIRouter(tags=["system"])


@router.get("/api/ready")
async def readiness() -> JSONResponse:
    """Readiness probe: 200 once the schema bootstrap is done, 503 until then."""
    if startup_state.ready:
        return JSONResponse(startup_state.snapshot())
    # A failed bootstrap will not fix itself, so don't tell clients to retry soon.
    retry_after = "30" if startup_state.phase == FAILED else "5"
    return JSONResponse(
        startup_state.snapshot(), status_code=503, headers={"Retry-After": retry_after}
    )
