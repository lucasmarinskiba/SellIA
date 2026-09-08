"""Shared async-to-sync bridge for Celery tasks.

Celery tasks run in worker threads/processes with no asyncio event loop by
default. A broken pattern was copy-pasted across ~17 task files in this
codebase (asyncio.get_event_loop() with an asyncio.run() fallback on
RuntimeError) that creates a FRESH event loop and closes it on every single
task invocation. That's fine for a completely stateless coroutine, but
AsyncSessionLocal's engine (app.core.database) -- and its underlying
asyncpg connection pool -- is a module-level singleton, lazily bound to
whichever event loop first used it. Once that first asyncio.run() call's
loop closes (which it always does when the coroutine finishes), every
SUBSEQUENT task in the same worker that reuses the same engine hits either
"Task <...> got Future <...> attached to a different loop" or
"RuntimeError: Event loop is closed" -- the engine is still bound to the
now-dead first loop. In production this showed up as every async Celery
task crash-looping and hammering Railway's log rate limit the moment the
celery worker/beat services were actually turned on for the first time.

Fix: one persistent event loop per worker THREAD, created lazily on first
use and never closed between tasks, so the async engine stays bound to the
same live loop for the worker thread's entire lifetime. threading.local()
keeps this correct even under a threaded/gevent/eventlet worker pool (a
prefork pool gets one loop per OS process naturally, since each worker
process has its own separate Python state).
"""

import asyncio
import threading

_local = threading.local()


def run_async(coro):
    """Run an async coroutine from a sync (Celery task) context.

    Reuses one persistent event loop per worker thread across calls --
    never closes it, unlike asyncio.run(). Safe to call repeatedly across
    many task invocations in the same worker process/thread.
    """
    loop = getattr(_local, "loop", None)
    if loop is None or loop.is_closed():
        loop = asyncio.new_event_loop()
        _local.loop = loop
    return loop.run_until_complete(coro)
