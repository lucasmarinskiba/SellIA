"""Computer Use — WebSocket Manager with Redis Pub/Sub

Maneja conexiones WebSocket de Computer Use con soporte para
múltiples workers usando Redis Pub/Sub como backplane.

En producción con uvicorn --workers 4, cada worker maneja sus propias
conexiones WebSocket. Para que el SessionManager (que puede estar en
otro worker) pueda enviar mensajes al cliente, usamos Redis Pub/Sub.
"""

import asyncio
import json
from typing import Dict, Optional
from uuid import UUID

import redis.asyncio as redis
from fastapi import WebSocket

from app.core.config import get_settings
from app.core.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class ComputerUseWebSocketManager:
    """Gestiona conexiones WebSocket con Redis Pub/Sub para multi-worker."""

    def __init__(self):
        self._connections: Dict[str, WebSocket] = {}
        self._redis: Optional[redis.Redis] = None
        self._pubsub: Optional[redis.client.PubSub] = None
        self._listener_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()

    async def _get_redis(self) -> redis.Redis:
        if self._redis is None:
            self._redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
        return self._redis

    async def start(self):
        """Inicia el listener de Redis Pub/Sub."""
        if self._listener_task and not self._listener_task.done():
            return
        self._listener_task = asyncio.create_task(self._listen_loop())
        logger.info("ComputerUseWebSocketManager started")

    async def stop(self):
        """Detiene el listener y cierra conexiones."""
        if self._listener_task:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass
            self._listener_task = None

        if self._pubsub:
            await self._pubsub.close()
        if self._redis:
            await self._redis.close()
            self._redis = None

        # Close all local WebSocket connections
        for ws in list(self._connections.values()):
            try:
                await ws.close()
            except Exception:
                pass
        self._connections.clear()
        logger.info("ComputerUseWebSocketManager stopped")

    async def connect(self, session_id: str, websocket: WebSocket):
        """Registra una conexión WebSocket local."""
        async with self._lock:
            self._connections[session_id] = websocket

        # Subscribe to Redis channel for this session
        redis_client = await self._get_redis()
        if self._pubsub:
            await self._pubsub.subscribe(f"cuws:{session_id}")

        logger.info(f"WS connected for session {session_id}")

    async def disconnect(self, session_id: str):
        """Desregistra una conexión WebSocket."""
        async with self._lock:
            self._connections.pop(session_id, None)

        # Unsubscribe from Redis channel
        if self._pubsub:
            try:
                await self._pubsub.unsubscribe(f"cuws:{session_id}")
            except Exception:
                pass

        logger.info(f"WS disconnected for session {session_id}")

    async def send_message(self, session_id: str, message: dict):
        """Envía un mensaje a un cliente vía WebSocket.

        Primero intenta enviar localmente. Si no está conectado localmente,
        publica en Redis para que otro worker lo envíe.
        """
        # Try local first
        ws = self._connections.get(session_id)
        if ws:
            try:
                await ws.send_json(message)
                return
            except Exception as e:
                logger.warning(f"Local WS send failed for {session_id}: {e}")
                # Connection might be broken, remove it
                async with self._lock:
                    self._connections.pop(session_id, None)

        # Publish to Redis for other workers
        try:
            redis_client = await self._get_redis()
            await redis_client.publish(
                f"cuws:{session_id}",
                json.dumps({"target": session_id, "message": message}),
            )
        except Exception as e:
            logger.error(f"Redis publish failed for {session_id}: {e}")

    async def _listen_loop(self):
        """Escucha mensajes de Redis y los reenvía a conexiones locales."""
        try:
            redis_client = await self._get_redis()
            self._pubsub = redis_client.pubsub()
            # Subscribe to all computer use ws channels
            await self._pubsub.psubscribe("cuws:*")

            async for msg in self._pubsub.listen():
                if msg["type"] == "pmessage":
                    try:
                        data = json.loads(msg["data"])
                        session_id = data.get("target")
                        message = data.get("message")
                        if session_id and message:
                            ws = self._connections.get(session_id)
                            if ws:
                                try:
                                    await ws.send_json(message)
                                except Exception as e:
                                    logger.warning(f"WS send via Redis failed: {e}")
                                    async with self._lock:
                                        self._connections.pop(session_id, None)
                    except Exception as e:
                        logger.error(f"Redis message handling error: {e}")
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"Redis listener error: {e}")
            # Restart after delay
            await asyncio.sleep(5)
            asyncio.create_task(self._listen_loop())


# Instancia global
ws_manager = ComputerUseWebSocketManager()
