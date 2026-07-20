"""Connection manager · in-process · pub via Redis for multi-instance."""
import asyncio
import json
import logging
from collections import defaultdict
from typing import Any

import redis.asyncio as aioredis
from fastapi import WebSocket

from app.core.config import settings


logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Per-process connections + Redis pub/sub for cross-process fanout.

    Channel naming: ws:tenant:{tenant_id} · ws:user:{user_id}.
    """

    def __init__(self):
        self._tenant_conns: dict[str, set[WebSocket]] = defaultdict(set)
        self._user_conns: dict[str, set[WebSocket]] = defaultdict(set)
        self._redis: aioredis.Redis | None = None
        self._pubsub_task: asyncio.Task | None = None

    async def _ensure_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
            self._pubsub_task = asyncio.create_task(self._listen_pubsub())
        return self._redis

    async def _listen_pubsub(self) -> None:
        """Subscribe to ws:* and fanout to local sockets."""
        assert self._redis is not None
        pubsub = self._redis.pubsub()
        await pubsub.psubscribe("ws:tenant:*", "ws:user:*")
        async for msg in pubsub.listen():
            if msg.get("type") != "pmessage":
                continue
            channel = msg["channel"]
            try:
                payload = json.loads(msg["data"])
            except Exception:
                continue

            if channel.startswith("ws:tenant:"):
                tid = channel.removeprefix("ws:tenant:")
                await self._fanout_local(self._tenant_conns.get(tid, set()), payload)
            elif channel.startswith("ws:user:"):
                uid = channel.removeprefix("ws:user:")
                await self._fanout_local(self._user_conns.get(uid, set()), payload)

    @staticmethod
    async def _fanout_local(sockets: set[WebSocket], payload: dict) -> None:
        dead = []
        for ws in sockets:
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            sockets.discard(ws)

    async def connect(self, ws: WebSocket, tenant_id: str, user_id: str) -> None:
        await self._ensure_redis()
        await ws.accept()
        self._tenant_conns[tenant_id].add(ws)
        self._user_conns[user_id].add(ws)
        logger.info("ws_connected", extra={"tenant_id": tenant_id, "user_id": user_id})

    def disconnect(self, ws: WebSocket, tenant_id: str, user_id: str) -> None:
        self._tenant_conns[tenant_id].discard(ws)
        self._user_conns[user_id].discard(ws)
        logger.info("ws_disconnected", extra={"tenant_id": tenant_id, "user_id": user_id})

    async def publish_tenant(self, tenant_id: str, payload: dict[str, Any]) -> None:
        r = await self._ensure_redis()
        await r.publish(f"ws:tenant:{tenant_id}", json.dumps(payload))

    async def publish_user(self, user_id: str, payload: dict[str, Any]) -> None:
        r = await self._ensure_redis()
        await r.publish(f"ws:user:{user_id}", json.dumps(payload))


manager = ConnectionManager()
