"""Celery tasks must run their coroutines through `app.core.async_bridge.run_async`.

`asyncio.run()` builds a fresh event loop and CLOSES it when the coroutine ends. The
async engine (and its asyncpg pool) is a module-level singleton, so after the first
task every pooled connection is bound to a dead loop and the next task dies with
`Task <...> got Future <...> attached to a different loop` or `Event loop is closed`.
In production that took down every task still calling `asyncio.run()`: pending crypto
payments, usage alerts, synthetic checks and others, on every run.

`run_async` keeps one persistent loop per worker thread. Most task modules had been
migrated; these tests make sure the rest stay migrated.
"""

from __future__ import annotations

import ast
import os
import pathlib

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

APP = pathlib.Path(__file__).resolve().parents[1] / "app"
BRIDGE = APP / "core" / "async_bridge.py"
_RAW_LOOP_CALLS = {"run", "get_event_loop", "new_event_loop"}

#: Task modules still on the broken pattern, with the reason they are not fixed yet.
#: The test fails if an entry here no longer needs to be, so this list can only shrink.
KNOWN_UNMIGRATED = {
    "domains/seo_config/tasks.py": "other sessions have uncommitted edits in seo_config/; migrate once they land",
}


def _is_celery_module(source: str) -> bool:
    return "shared_task" in source or "celery_app.task" in source or "@app.task" in source


def _raw_loop_calls(path: pathlib.Path) -> list[int]:
    """Line numbers of asyncio.run / get_event_loop / new_event_loop calls."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    lines = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in _RAW_LOOP_CALLS
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "asyncio"
        ):
            lines.append(node.lineno)
    return lines


def _celery_modules() -> list[pathlib.Path]:
    out = []
    for path in sorted(APP.rglob("*.py")):
        if path == BRIDGE or "__pycache__" in path.parts:
            continue
        if _is_celery_module(path.read_text(encoding="utf-8", errors="replace")):
            out.append(path)
    return out


def test_no_celery_task_uses_a_raw_event_loop() -> None:
    offenders = {}
    for path in _celery_modules():
        rel = path.relative_to(APP).as_posix()
        lines = _raw_loop_calls(path)
        if lines and rel not in KNOWN_UNMIGRATED:
            offenders[rel] = lines
    assert not offenders, (
        "Celery task modules must use app.core.async_bridge.run_async, not asyncio.run / "
        f"get_event_loop / new_event_loop (see this file's docstring): {offenders}"
    )


def test_known_unmigrated_list_has_no_stale_entries() -> None:
    stale = [
        rel for rel in KNOWN_UNMIGRATED
        if not (APP / rel).exists() or not _raw_loop_calls(APP / rel)
    ]
    assert not stale, f"Already migrated, remove from KNOWN_UNMIGRATED: {stale}"


# ── behaviour: a pooled engine survives consecutive tasks only through the bridge ──

def _pooled_engine():
    """A real pooled engine, like the app's: connections outlive a single coroutine."""
    return create_async_engine(os.environ["DATABASE_URL"], pool_size=2, max_overflow=0)


def test_bridge_keeps_a_pooled_engine_working_across_consecutive_tasks() -> None:
    from app.core.async_bridge import run_async

    engine = _pooled_engine()

    async def one_task() -> int:
        async with engine.connect() as conn:
            return (await conn.execute(text("select 1"))).scalar_one()

    try:
        assert [run_async(one_task()) for _ in range(5)] == [1] * 5
    finally:
        run_async(engine.dispose())


def test_asyncio_run_breaks_the_same_pooled_engine() -> None:
    """Documents why the bridge exists: the exact failure the workers logged."""
    import asyncio

    engine = _pooled_engine()

    async def one_task() -> int:
        async with engine.connect() as conn:
            return (await conn.execute(text("select 1"))).scalar_one()

    failures = []
    for _ in range(4):
        try:
            asyncio.run(one_task())
        except Exception as exc:  # noqa: BLE001 -- the failure type varies with timing
            failures.append(type(exc).__name__)
    pytest.importorskip("asyncpg")
    assert failures, "expected a 'different loop' / 'Event loop is closed' failure on reuse"
