"""Brain Activity Bus — telemetría REAL de interacciones del cerebro.

Registro en memoria (ring buffer) de interacciones que ocurren de verdad en el
sistema: un agente usa una skill, se consulta la base de conocimiento, se abre
una sesión de Computer Use, se procesa una señal de copy-trade, etc.

NO inventa eventos. El NeuralBrain del frontend consume `recent()` para
"disparar" sólo las sinapsis que de verdad sucedieron; si no hay actividad, el
grafo queda idle (sin fuego), nunca con interacciones falsas.

Diseño:
  * Proceso-local, thread-safe (lock), sin dependencias externas.
  * `record(...)` es barato y best-effort: nunca rompe el camino caliente.
  * Cada evento referencia ids de nodos del grafo de capacidades
    (ver `registry.graph()`), de modo que el frontend mapea evento → edge real.
"""

from __future__ import annotations

import threading
import time
from collections import deque
from dataclasses import dataclass, asdict
from typing import Any, Deque, Optional

from app.core.logger import get_logger

logger = get_logger(__name__)

# Tipos de interacción reales que el sistema puede emitir.
_KINDS = frozenset({
    "agent",        # un agente toma el control / razona
    "skill",        # se usa una skill (conocimiento, tool)
    "knowledge",    # consulta a la base de conocimiento
    "automation",   # corre una automatización
    "computer_use", # acción de Computer Use (navegador/sandbox)
    "db",           # lectura/escritura a base de datos
    "function",     # llamada a función/tool del orquestador
})

_MAX_EVENTS = 300


@dataclass(frozen=True)
class ActivityEvent:
    """Una interacción real, lista para serializar al frontend."""
    seq: int
    ts: float                  # epoch segundos
    kind: str                  # uno de _KINDS
    source: str                # id de nodo origen (capability id o canal)
    target: Optional[str]      # id de nodo destino (None = self-activación)
    detail: str                # descripción corta y honesta

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class BrainActivityBus:
    """Ring buffer thread-safe de eventos reales."""

    def __init__(self, maxlen: int = _MAX_EVENTS) -> None:
        self._events: Deque[ActivityEvent] = deque(maxlen=maxlen)
        self._lock = threading.Lock()
        self._seq = 0

    def record(
        self,
        kind: str,
        source: str,
        detail: str,
        target: Optional[str] = None,
    ) -> None:
        """Registra un evento real. Best-effort: nunca lanza."""
        try:
            if kind not in _KINDS:
                kind = "function"
            with self._lock:
                self._seq += 1
                self._events.append(ActivityEvent(
                    seq=self._seq,
                    ts=time.time(),
                    kind=kind,
                    source=str(source),
                    target=str(target) if target else None,
                    detail=str(detail)[:160],
                ))
        except Exception as exc:  # pragma: no cover - defensivo
            logger.debug("activity record failed: %s", exc)

    def recent(self, limit: int = 40, since_seq: int = 0) -> list[dict[str, Any]]:
        """Eventos más recientes (opcionalmente sólo posteriores a `since_seq`)."""
        with self._lock:
            evs = [e for e in self._events if e.seq > since_seq]
        return [e.as_dict() for e in evs[-limit:]]

    def stats(self) -> dict[str, Any]:
        with self._lock:
            evs = list(self._events)
        by_kind: dict[str, int] = {}
        for e in evs:
            by_kind[e.kind] = by_kind.get(e.kind, 0) + 1
        last_ts = evs[-1].ts if evs else None
        return {
            "total": self._seq,
            "buffered": len(evs),
            "by_kind": by_kind,
            "last_ts": last_ts,
        }


class CuaFlowStore:
    """Almacena flujos de Computer Use despachados (sesiones), para la vista n8n.

    Cada flujo = una indicación del usuario convertida en pasos planificados
    (trigger → agentes/tools/plataformas). En memoria, ring buffer.
    """

    def __init__(self, maxlen: int = 30) -> None:
        self._flows: Deque[dict[str, Any]] = deque(maxlen=maxlen)
        self._lock = threading.Lock()
        self._seq = 0

    def add(self, flow: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            self._seq += 1
            flow = {**flow, "seq": self._seq, "ts": time.time()}
            self._flows.append(flow)
        return flow

    def recent(self, limit: int = 20) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._flows)[-limit:]


_cua_store: Optional[CuaFlowStore] = None
_bus: Optional[BrainActivityBus] = None
_bus_lock = threading.Lock()


def get_cua_store() -> CuaFlowStore:
    global _cua_store
    if _cua_store is None:
        with _bus_lock:
            if _cua_store is None:
                _cua_store = CuaFlowStore()
    return _cua_store


def get_activity_bus() -> BrainActivityBus:
    global _bus
    if _bus is None:
        with _bus_lock:
            if _bus is None:
                _bus = BrainActivityBus()
    return _bus


def record_activity(kind: str, source: str, detail: str, target: Optional[str] = None) -> None:
    """Atajo best-effort para emitir un evento real desde cualquier capa."""
    get_activity_bus().record(kind=kind, source=source, detail=detail, target=target)
