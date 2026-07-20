"""Event Bus — Redis Pub/Sub para desacoplar dominios.

Permite que agentes, automatizaciones, canales y CRM se comuniquen
mediante eventos sin acoplamiento directo.
"""

import json
import asyncio
from typing import Any, Callable, Dict, List, Optional, Coroutine
from datetime import datetime, timezone

import redis.asyncio as redis
from app.core.config import get_settings

settings = get_settings()

# Tipos
EventHandler = Callable[[Dict[str, Any]], Coroutine[Any, Any, None]]


class EventBus:
    """Bus de eventos async basado en Redis Pub/Sub."""

    _instance: Optional["EventBus"] = None
    _redis_pool: Optional[redis.Redis] = None
    _handlers: Dict[str, List[EventHandler]] = {}
    _pubsub: Optional[redis.client.PubSub] = None
    _listener_task: Optional[asyncio.Task] = None

    def __new__(cls) -> "EventBus":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def connect(self):
        """Inicializar conexión Redis."""
        if self._redis_pool is None:
            self._redis_pool = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
            )
        return self._redis_pool

    async def disconnect(self):
        """Cerrar conexiones."""
        if self._pubsub:
            await self._pubsub.close()
        if self._redis_pool:
            await self._redis_pool.close()
            self._redis_pool = None

    async def publish(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Publicar un evento en Redis."""
        await self.connect()
        message = {
            "event_type": event_type,
            "payload": payload,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await self._redis_pool.publish(f"events:{event_type}", json.dumps(message))
        # También publicar en canal general para listeners wildcard
        await self._redis_pool.publish("events:all", json.dumps(message))

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Suscribir un handler a un tipo de evento (en memoria)."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """Desuscribir un handler."""
        if event_type in self._handlers:
            self._handlers[event_type] = [h for h in self._handlers[event_type] if h != handler]

    async def start_listener(self):
        """Iniciar listener de Redis Pub/Sub en background."""
        if self._listener_task and not self._listener_task.done():
            return
        self._listener_task = asyncio.create_task(self._listen_loop())

    async def stop_listener(self):
        """Detener listener."""
        if self._listener_task:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass
            self._listener_task = None

    async def _listen_loop(self):
        """Loop principal de escucha Redis."""
        await self.connect()
        self._pubsub = self._redis_pool.pubsub()
        # Suscribir a todos los canales de eventos
        channels = [f"events:{et}" for et in self._handlers.keys()] + ["events:all"]
        if channels:
            await self._pubsub.subscribe(*channels)

        async for message in self._pubsub.listen():
            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                    event_type = data.get("event_type", "")
                    payload = data.get("payload", {})
                    # Ejecutar handlers in-memory
                    handlers = self._handlers.get(event_type, [])
                    for handler in handlers:
                        try:
                            asyncio.create_task(handler(payload))
                        except Exception as e:
                            from app.core.logger import get_logger
                            get_logger(__name__).error(f"Handler error for {event_type}: {e}")
                except Exception as e:
                    from app.core.logger import get_logger
                    get_logger(__name__).error(f"Message parse error: {e}")

    async def emit(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Emitir evento: publica en Redis Y ejecuta handlers in-memory inmediatamente."""
        await self.publish(event_type, payload)
        # Ejecutar handlers locales inmediatamente (para no depender del round-trip Redis)
        handlers = self._handlers.get(event_type, [])
        for handler in handlers:
            try:
                asyncio.create_task(handler(payload))
            except Exception as e:
                from app.core.logger import get_logger
                get_logger(__name__).error(f"Local handler error for {event_type}: {e}")


# Instancia global
event_bus = EventBus()


async def emit_event(event_type: str, payload: Dict[str, Any]) -> None:
    """Helper para emitir eventos usando el event bus global."""
    await event_bus.emit(event_type, payload)


# ===== Helpers de eventos comunes =====

async def emit_message_received(
    business_id: str,
    conversation_id: str,
    platform: str,
    content: str,
    sender_name: Optional[str] = None,
    is_new_conversation: bool = False,
):
    await event_bus.emit("message.received", {
        "business_id": business_id,
        "conversation_id": conversation_id,
        "platform": platform,
        "content": content,
        "sender_name": sender_name,
        "is_new_conversation": is_new_conversation,
    })


async def emit_message_sent(
    business_id: str,
    conversation_id: str,
    platform: str,
    content: str,
):
    await event_bus.emit("message.sent", {
        "business_id": business_id,
        "conversation_id": conversation_id,
        "platform": platform,
        "content": content,
    })


async def emit_lead_score_changed(
    business_id: str,
    conversation_id: str,
    old_score: int,
    new_score: int,
    old_classification: str,
    new_classification: str,
):
    await event_bus.emit("lead.score_changed", {
        "business_id": business_id,
        "conversation_id": conversation_id,
        "old_score": old_score,
        "new_score": new_score,
        "old_classification": old_classification,
        "new_classification": new_classification,
    })


async def emit_deal_created(
    business_id: str,
    deal_id: str,
    conversation_id: Optional[str] = None,
    value: Optional[float] = None,
    stage: str = "new_lead",
):
    await event_bus.emit("deal.created", {
        "business_id": business_id,
        "deal_id": deal_id,
        "conversation_id": conversation_id,
        "value": value,
        "stage": stage,
    })


async def emit_workflow_completed(
    business_id: str,
    workflow_id: str,
    execution_id: str,
    status: str,
    conversation_id: Optional[str] = None,
):
    await event_bus.emit("workflow.completed", {
        "business_id": business_id,
        "workflow_id": workflow_id,
        "execution_id": execution_id,
        "status": status,
        "conversation_id": conversation_id,
    })


async def emit_human_handoff_required(
    business_id: str,
    conversation_id: str,
    platform: str,
    reason: str,
    lead_name: Optional[str] = None,
):
    await event_bus.emit("human.handoff_required", {
        "business_id": business_id,
        "conversation_id": conversation_id,
        "platform": platform,
        "reason": reason,
        "lead_name": lead_name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


async def emit_order_created(
    business_id: str,
    order_id: str,
    total_amount: float,
    status: str,
    conversation_id: Optional[str] = None,
):
    await event_bus.emit("order.created", {
        "business_id": business_id,
        "order_id": order_id,
        "total_amount": total_amount,
        "status": status,
        "conversation_id": conversation_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


async def emit_revenue_event(
    business_id: str,
    revenue_event_id: str,
    amount: float,
    event_type: str,
):
    await event_bus.emit("revenue.event", {
        "business_id": business_id,
        "revenue_event_id": revenue_event_id,
        "amount": amount,
        "event_type": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
