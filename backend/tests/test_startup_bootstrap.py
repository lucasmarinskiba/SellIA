"""The app must serve before its schema bootstrap finishes.

History: the lifespan ran ~30 bootstrap blocks (ensure_all_tables creating ~400
tables one transaction at a time, seed_personalities doing 2 round trips for each
of 506 personalities, ...) BEFORE yielding, and uvicorn does not bind its port
until the lifespan yields. Every Railway deploy/restart therefore answered 502 --
/api/health included -- for ~13 minutes, and the E2E job's backend never became
reachable within its budget.

These tests pin the new contract:
  * the lifespan yields while the bootstrap is still running;
  * /api/health (liveness) answers 200 meanwhile, /api/ready (readiness) is 503
    until the bootstrap is done, then 200;
  * the loops that depend on the schema start only after the bootstrap;
  * a failed bootstrap keeps the process alive but never reports ready;
plus the round-trip regressions that made the bootstrap slow in the first place.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from types import SimpleNamespace

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy import delete, event, func, select

from app import sellbot
from app.core import startup_state as ss

# ── StartupState ─────────────────────────────────────────────────────────────

def test_state_lifecycle() -> None:
    state = ss.StartupState()
    assert state.phase == ss.PENDING
    assert not state.ready and not state.done
    assert state.elapsed_seconds is None

    state.start()
    state.mark("init_db")
    assert state.phase == ss.RUNNING
    assert not state.ready and not state.done
    assert "init_db" in state.snapshot()["steps"]

    state.complete()
    assert state.ready and state.done
    assert state.snapshot()["ready"] is True
    assert state.elapsed_seconds is not None


def test_state_failure_is_done_but_not_ready() -> None:
    state = ss.StartupState()
    state.start()
    state.fail(RuntimeError("boom"))
    assert state.done and not state.ready
    assert state.phase == ss.FAILED
    assert "boom" in (state.error or "")


def test_mark_before_start_is_ignored() -> None:
    state = ss.StartupState()
    state.mark("early")
    assert state.snapshot()["steps"] == {}


async def test_ready_route_follows_the_state(monkeypatch: pytest.MonkeyPatch) -> None:
    state = ss.StartupState()
    monkeypatch.setattr(ss, "startup_state", state)
    app = FastAPI()
    app.include_router(ss.router)

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t") as c:
        r = await c.get("/api/ready")
        assert r.status_code == 503 and r.json()["phase"] == ss.PENDING

        state.start()
        r = await c.get("/api/ready")
        assert r.status_code == 503 and r.headers["retry-after"] == "5"

        state.complete()
        r = await c.get("/api/ready")
        assert r.status_code == 200 and r.json()["ready"] is True


# ── lifespan: yields before the bootstrap finishes ───────────────────────────

@pytest.fixture
def lifespan_env(monkeypatch: pytest.MonkeyPatch):
    """Swap every external collaborator of the lifespan for an inert fake."""
    state = ss.StartupState()
    monkeypatch.setattr(ss, "startup_state", state)
    monkeypatch.setattr(sellbot, "startup_state", state)

    class FakeScheduler:
        redis = None

        async def close(self) -> None:
            return None

    async def fake_get_scheduler() -> FakeScheduler:
        return FakeScheduler()

    async def fake_init(scheduler: object) -> SimpleNamespace:
        return SimpleNamespace(running=True, scheduler=scheduler)

    async def noop() -> None:
        return None

    started: list[str] = []

    async def fake_start_processor() -> None:
        started.append("processor")

    async def fake_followup_loop() -> None:
        started.append("followup")

    # The lifespan assigns these module globals; registering them here makes
    # monkeypatch put the originals back so the fakes never leak into other tests.
    for name in ("scheduler", "processor", "progression_service"):
        monkeypatch.setattr(sellbot, name, None)

    monkeypatch.setattr(sellbot, "get_scheduler", fake_get_scheduler)
    monkeypatch.setattr(sellbot, "init_processor", fake_init)
    monkeypatch.setattr(sellbot, "init_progression_service", fake_init)
    monkeypatch.setattr(sellbot, "start_processor", fake_start_processor)
    monkeypatch.setattr(sellbot, "run_followup_loop", fake_followup_loop)
    monkeypatch.setattr(sellbot, "stop_processor", noop)
    monkeypatch.setattr(sellbot, "stop_followup_loop", lambda: None)
    monkeypatch.setattr(sellbot, "close_db", noop)  # don't dispose the shared engine

    class FakeSession:
        async def execute(self, *_: object) -> None:
            return None

    async def fake_get_db():
        yield FakeSession()

    sellbot.app.dependency_overrides[sellbot.get_db] = fake_get_db
    yield SimpleNamespace(state=state, started=started)
    sellbot.app.dependency_overrides.pop(sellbot.get_db, None)


async def _until(predicate: Callable[[], bool], timeout: float = 5.0) -> None:
    async def poll() -> None:
        while not predicate():
            await asyncio.sleep(0.01)

    await asyncio.wait_for(poll(), timeout)


def _client() -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=sellbot.app), base_url="http://t")


async def test_lifespan_yields_while_bootstrap_still_runs(
    monkeypatch: pytest.MonkeyPatch, lifespan_env: SimpleNamespace
) -> None:
    gate = asyncio.Event()

    async def blocked_bootstrap() -> None:
        await gate.wait()

    monkeypatch.setattr(sellbot, "_bootstrap_database", blocked_bootstrap)
    state, started = lifespan_env.state, lifespan_env.started

    # If the lifespan awaited the bootstrap this would hang until the timeout.
    async with asyncio.timeout(5):
        async with sellbot.lifespan(sellbot.app):
            assert state.phase == ss.RUNNING
            assert started == [], "schema-dependent loops must wait for the bootstrap"

            async with _client() as c:
                health = await c.get("/api/health")
                assert health.status_code == 200
                assert health.json()["components"]["bootstrap"] == ss.RUNNING

                ready = await c.get("/api/ready")
                assert ready.status_code == 503
                assert ready.json()["ready"] is False

                gate.set()
                await _until(lambda: state.done)
                await _until(lambda: len(started) == 2)  # let the create_task'd loops run

                ready = await c.get("/api/ready")
                assert ready.status_code == 200
                assert (await c.get("/api/health")).json()["components"]["bootstrap"] == ss.COMPLETE

    assert set(started) == {"processor", "followup"}


async def test_failed_bootstrap_keeps_serving_but_never_reports_ready(
    monkeypatch: pytest.MonkeyPatch, lifespan_env: SimpleNamespace
) -> None:
    async def broken_bootstrap() -> None:
        raise RuntimeError("schema exploded")

    monkeypatch.setattr(sellbot, "_bootstrap_database", broken_bootstrap)
    state, started = lifespan_env.state, lifespan_env.started

    async with asyncio.timeout(5):
        async with sellbot.lifespan(sellbot.app):
            await _until(lambda: state.done)
            async with _client() as c:
                assert (await c.get("/api/health")).status_code == 200
                ready = await c.get("/api/ready")
                assert ready.status_code == 503
                assert ready.json()["phase"] == ss.FAILED
                assert "schema exploded" in ready.json()["error"]
                assert ready.headers["retry-after"] == "30"

    assert started == []


async def test_shutdown_cancels_a_bootstrap_that_is_still_running(
    monkeypatch: pytest.MonkeyPatch, lifespan_env: SimpleNamespace
) -> None:
    cancelled = asyncio.Event()

    async def endless_bootstrap() -> None:
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            cancelled.set()
            raise

    monkeypatch.setattr(sellbot, "_bootstrap_database", endless_bootstrap)

    async with asyncio.timeout(5):
        async with sellbot.lifespan(sellbot.app):
            await asyncio.sleep(0.05)  # let the task start awaiting
        # leaving the context is the shutdown; it must not hang on the task

    assert cancelled.is_set()
    assert lifespan_env.state.phase == ss.RUNNING  # never claims ready


async def test_health_is_not_held_up_by_a_stuck_database(
    monkeypatch: pytest.MonkeyPatch, lifespan_env: SimpleNamespace
) -> None:
    """A saturated pool must not hold the liveness probe past its own timeout."""

    class HangingSession:
        async def execute(self, *_: object) -> None:
            await asyncio.Event().wait()

    async def hanging_get_db():
        yield HangingSession()

    sellbot.app.dependency_overrides[sellbot.get_db] = hanging_get_db
    async with asyncio.timeout(10):
        async with _client() as c:
            r = await c.get("/api/health")
    assert r.status_code == 200
    assert r.json()["components"]["database"] == "timeout"


# ── the round trips that made the bootstrap take minutes ─────────────────────

def _count_statements(engine, matching: Callable[[str], bool] = lambda _: True):
    """Context-manager-ish: returns (list, remove) recording cursor statements."""
    seen: list[str] = []

    def record(conn, cursor, statement, parameters, context, executemany) -> None:
        if matching(statement):
            seen.append(statement)

    event.listen(engine.sync_engine, "before_cursor_execute", record)
    return seen, lambda: event.remove(engine.sync_engine, "before_cursor_execute", record)


async def test_seed_personalities_is_bulk_idempotent_and_keeps_existing_rows(db_session) -> None:
    from app.domains.agents.models import AgentPersonality
    from app.domains.agents.services import AgentService

    await db_session.execute(delete(AgentPersonality))
    await db_session.commit()
    try:
        # A row an operator may have edited: seeding must not overwrite it.
        db_session.add(AgentPersonality(
            slug="alex-hormozi", name="Edited by hand", tagline="t", description="d",
        ))
        await db_session.commit()

        service = AgentService(db_session)
        first = await service.seed_personalities()

        total = (await db_session.execute(select(func.count()).select_from(AgentPersonality))).scalar_one()
        assert total > 400, "the curated catalogue was not seeded"
        assert len({p.slug for p in first}) == total

        edited = (await db_session.execute(
            select(AgentPersonality).where(AgentPersonality.slug == "alex-hormozi")
        )).scalar_one()
        assert edited.name == "Edited by hand"

        ids_before = {p.slug: p.id for p in first}

        # Steady state (everything already seeded): a handful of statements,
        # not ~2 per personality. 506 x 2 round trips was minutes on Railway.
        seen, remove = _count_statements(db_session.bind)
        try:
            again = await service.seed_personalities()
        finally:
            remove()
        assert len(seen) <= 4, f"{len(seen)} statements for an already-seeded catalogue"
        assert {p.slug: p.id for p in again} == ids_before
    finally:
        await db_session.execute(delete(AgentPersonality))
        await db_session.commit()


async def test_existing_table_names_lists_tables_and_reports_unknown_as_none(db_session) -> None:
    from sqlalchemy.ext.asyncio import create_async_engine

    from app.db.schema_bootstrap import existing_table_names

    names = await existing_table_names(db_session.bind)
    assert names is not None and "agent_personalities" in names

    unreachable = create_async_engine("postgresql+asyncpg://nobody:x@127.0.0.1:1/none")
    try:
        assert await existing_table_names(unreachable) is None
    finally:
        await unreachable.dispose()


def test_every_brand_transformation_column_patch_is_recognised() -> None:
    """If the pattern stops matching a patch, it silently reverts to an
    unconditional ALTER TABLE (an ACCESS EXCLUSIVE lock) on every boot."""
    from app.domains.brand_transformation.bootstrap import (
        _COLUMN_PATCHES,
        _PATCH_TARGET,
    )

    unparsed = [s for s in _COLUMN_PATCHES if not _PATCH_TARGET.match(s)]
    assert unparsed == []


async def test_brand_transformation_bootstrap_takes_no_alter_locks_once_patched(db_session) -> None:
    from app.core.database import engine
    from app.domains.brand_transformation.bootstrap import (
        ensure_brand_transformation_tables,
    )

    await ensure_brand_transformation_tables()  # brings any missing column in

    seen, remove = _count_statements(engine, lambda s: s.lstrip().upper().startswith("ALTER TABLE"))
    try:
        await ensure_brand_transformation_tables()
    finally:
        remove()
    assert seen == [], f"already-patched tables were ALTERed again: {seen[:3]}"
