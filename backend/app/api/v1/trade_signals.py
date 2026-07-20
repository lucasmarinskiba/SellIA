"""Copy-Trade supervisado — API Router.

Expone la capa de soporte de decisión (`trade_signals`) al frontend SellIA.

Invariante de seguridad (no negociable): el agente ANALIZA y PROPONE; el
usuario debe estar ACTIVO (heartbeat) y aprobar/rechazar. Al aprobar, se
devuelve un *handoff* para que el USUARIO ejecute la orden en su plataforma.
El backend NUNCA ejecuta compras/ventas ni mueve fondos.

Estado respaldado en Redis (presencia + cola), compartido entre procesos y
persistente entre reinicios. Postura fail-closed: si Redis no responde, no se
proponen ni aprueban operaciones.
"""

from __future__ import annotations

from typing import List, Optional

import redis.asyncio as redis
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.core.deps import get_current_active_user, RateLimit
from app.domains.users.models import User
from app.domains.computer_use.skills import (
    AssetClass,
    TradeSide,
    AnalysisStyle,
    RiskRating,
    TradeProposal,
    ANALYSIS_BY_ASSET,
)
from app.domains.computer_use.skills.trade_store import RedisCopyTradeStore

settings = get_settings()
router = APIRouter()


# ── store respaldado en Redis (compartido entre procesos) ─────────────────
_store: Optional[RedisCopyTradeStore] = None


def get_store() -> RedisCopyTradeStore:
    global _store
    if _store is None:
        # Cliente endurecido: timeouts acotados + health-check de conexión +
        # reintento ante desconexión → evita cuelgues y degradación silenciosa.
        client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5,
            health_check_interval=30,
            retry_on_timeout=True,
        )
        _store = RedisCopyTradeStore(client)
    return _store


# ── schemas ──────────────────────────────────────────────────────────────
class TradeProposalCreate(BaseModel):
    asset: str = Field(..., min_length=1, max_length=120)
    asset_class: AssetClass
    side: TradeSide
    rationale: str = Field(..., min_length=1, max_length=2000)
    analysis_styles: List[AnalysisStyle] = Field(default_factory=list)
    risk: RiskRating
    confidence: float = Field(..., ge=0.0, le=1.0)
    market: str = Field("", max_length=120)
    suggested_allocation_pct: Optional[float] = Field(None, ge=0.0, le=100.0)
    stop_loss: Optional[str] = Field(None, max_length=120)
    take_profit: Optional[str] = Field(None, max_length=120)
    ttl_sec: Optional[int] = Field(None, ge=1, le=86400)


# ── presencia ─────────────────────────────────────────────────────────────
@router.post(
    "/trade/heartbeat",
    dependencies=[Depends(RateLimit(times=60, seconds=60))],
)
async def trade_heartbeat(
    user: User = Depends(get_current_active_user),
    store: RedisCopyTradeStore = Depends(get_store),
) -> dict:
    """Registra presencia activa del usuario (debe latir periódicamente).

    Fail-closed: si Redis no responde, devuelve 503 (no se finge presencia).
    """
    ok = await store.heartbeat(str(user.id))
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servicio de copy-trade temporalmente no disponible.",
        )
    return {"active": await store.is_active(str(user.id)), "window_sec": store.window_sec}


@router.get(
    "/trade/presence",
    dependencies=[Depends(RateLimit(times=60, seconds=60))],
)
async def trade_presence(
    user: User = Depends(get_current_active_user),
    store: RedisCopyTradeStore = Depends(get_store),
) -> dict:
    return {"active": await store.is_active(str(user.id)), "window_sec": store.window_sec}


# ── propuestas ─────────────────────────────────────────────────────────────
@router.post(
    "/trade/proposals",
    dependencies=[Depends(RateLimit(times=30, seconds=60))],
)
async def submit_proposal(
    body: TradeProposalCreate,
    user: User = Depends(get_current_active_user),
    store: RedisCopyTradeStore = Depends(get_store),
) -> dict:
    """Encola una propuesta. Requiere usuario ACTIVO (heartbeat reciente)."""
    kwargs = body.model_dump(exclude_none=True)
    proposal = TradeProposal(**kwargs)
    res = await store.submit(str(user.id), proposal)
    if not res["accepted"]:
        raise HTTPException(status_code=409, detail=res["reason"])
    return res


@router.get(
    "/trade/proposals",
    dependencies=[Depends(RateLimit(times=60, seconds=60))],
)
async def list_pending(
    user: User = Depends(get_current_active_user),
    store: RedisCopyTradeStore = Depends(get_store),
) -> dict:
    """Propuestas pendientes. Vacío si el usuario está inactivo."""
    items = await store.pending(str(user.id))
    return {"count": len(items), "items": items}


@router.post(
    "/trade/proposals/{proposal_id}/approve",
    dependencies=[Depends(RateLimit(times=30, seconds=60))],
)
async def approve_proposal(
    proposal_id: str,
    user: User = Depends(get_current_active_user),
    store: RedisCopyTradeStore = Depends(get_store),
) -> dict:
    """Aprueba una propuesta y devuelve el handoff de ejecución para el USUARIO.

    El backend NO ejecuta la orden: `handoff.agent_executes` es siempre False.
    """
    res = await store.approve(str(user.id), proposal_id)
    if not res["ok"]:
        raise HTTPException(status_code=409, detail=res["reason"])
    return res


@router.post(
    "/trade/proposals/{proposal_id}/reject",
    dependencies=[Depends(RateLimit(times=30, seconds=60))],
)
async def reject_proposal(
    proposal_id: str,
    user: User = Depends(get_current_active_user),
    store: RedisCopyTradeStore = Depends(get_store),
) -> dict:
    res = await store.reject(str(user.id), proposal_id)
    if not res["ok"]:
        raise HTTPException(status_code=409, detail=res["reason"])
    return res


@router.get("/trade/analysis-styles")
async def analysis_styles() -> dict:
    """Estilos de análisis válidos por clase de activo (introspección)."""
    return {
        ac.value: [s.value for s in styles]
        for ac, styles in ANALYSIS_BY_ASSET.items()
    }
