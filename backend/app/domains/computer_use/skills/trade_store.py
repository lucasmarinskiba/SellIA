"""Copy-Trade — almacén respaldado en Redis.

Reemplaza el estado in-memory por uno persistente y compartido entre procesos
(escala horizontal + sobrevive reinicios). Mantiene el MISMO contrato e
invariante de seguridad que ``CopyTradeReviewQueue``: el backend nunca ejecuta;
``approve`` solo devuelve el handoff para que el USUARIO opere.

Claves Redis:
  * ``ct:presence:{user_id}``   — string con TTL = ventana de presencia.
  * ``ct:proposals:{user_id}``  — hash {proposal_id → JSON de estado}.

El cliente Redis se inyecta (testeable). En producción se usa el singleton
``redis.from_url(settings.REDIS_URL)``.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import List, Optional

from redis.exceptions import RedisError

from app.core.logger import get_logger
from app.domains.computer_use.skills.trade_signals import (
    TradeProposal,
    ProposalStatus,
    DEFAULT_PRESENCE_WINDOW_SEC,
)

logger = get_logger(__name__)

# Mensaje único cuando Redis no responde. Postura fail-closed: ante fallo de
# infraestructura, se DENIEGA (no se proponen ni aprueban operaciones).
_UNAVAILABLE = "Servicio de copy-trade temporalmente no disponible."


def _presence_key(user_id: str) -> str:
    return f"ct:presence:{user_id}"


def _proposals_key(user_id: str) -> str:
    return f"ct:proposals:{user_id}"


# Red de seguridad anti-fuga: la clave del hash de propuestas se autodestruye
# tras este lapso de inactividad de escritura (las propuestas viven minutos).
PROPOSALS_KEY_TTL_SEC = 86_400  # 24h


class RedisCopyTradeStore:
    """Cola copy-trade persistente. API async equivalente a CopyTradeReviewQueue."""

    def __init__(self, redis_client, window_sec: int = DEFAULT_PRESENCE_WINDOW_SEC):
        self.redis = redis_client
        self.window_sec = window_sec

    # ── presencia ────────────────────────────────────────────────────────
    async def heartbeat(self, user_id: str) -> bool:
        try:
            await self.redis.setex(_presence_key(user_id), self.window_sec, "1")
            return True
        except RedisError as e:
            logger.error(f"copy-trade heartbeat redis error: {e}")
            return False

    async def is_active(self, user_id: str) -> bool:
        # Fail-closed: si Redis no responde, el usuario NO está activo.
        try:
            return bool(await self.redis.exists(_presence_key(user_id)))
        except RedisError as e:
            logger.error(f"copy-trade is_active redis error: {e}")
            return False

    # ── propuestas ───────────────────────────────────────────────────────
    async def submit(self, user_id: str, proposal: TradeProposal) -> dict:
        if not await self.is_active(user_id):
            return {
                "accepted": False,
                "reason": "Usuario inactivo: se requiere presencia activa para proponer operaciones.",
            }
        try:
            await self._save(user_id, proposal)
        except RedisError as e:
            logger.error(f"copy-trade submit redis error: {e}")
            return {"accepted": False, "reason": _UNAVAILABLE}
        return {"accepted": True, "proposal": proposal.to_dict()}

    async def _load(self, user_id: str, proposal_id: str) -> Optional[TradeProposal]:
        raw = await self.redis.hget(_proposals_key(user_id), proposal_id)
        if raw is None:
            return None
        return TradeProposal.from_state(json.loads(raw))

    async def _save(self, user_id: str, proposal: TradeProposal) -> None:
        key = _proposals_key(user_id)
        await self.redis.hset(key, proposal.id, json.dumps(proposal.to_state()))
        # TTL rodante: cada escritura renueva la expiración del hash → impide
        # crecimiento ilimitado si el usuario abandona propuestas terminales.
        await self.redis.expire(key, PROPOSALS_KEY_TTL_SEC)

    async def pending(self, user_id: str, now: Optional[datetime] = None) -> List[dict]:
        if not await self.is_active(user_id):
            return []
        try:
            raw = await self.redis.hgetall(_proposals_key(user_id))
            out: List[dict] = []
            for pid, payload in (raw or {}).items():
                p = TradeProposal.from_state(json.loads(payload))
                if p.status == ProposalStatus.PENDING and p.is_expired(now):
                    # Expirada: se purga del hash para acotar el crecimiento.
                    await self.redis.hdel(_proposals_key(user_id), pid)
                    continue
                if p.status == ProposalStatus.PENDING:
                    out.append(p.to_dict())
            return out
        except RedisError as e:
            logger.error(f"copy-trade pending redis error: {e}")
            return []

    async def approve(self, user_id: str, proposal_id: str, now: Optional[datetime] = None) -> dict:
        try:
            p = await self._load(user_id, proposal_id)
            if p is None:
                return {"ok": False, "reason": "Propuesta no encontrada."}
            if not await self.is_active(user_id):
                return {"ok": False, "reason": "Usuario inactivo: no se puede aprobar sin presencia."}
            if p.is_expired(now):
                p.status = ProposalStatus.EXPIRED
                await self._save(user_id, p)
                return {"ok": False, "reason": "Propuesta expirada; el mercado se movió."}
            if p.status != ProposalStatus.PENDING:
                return {"ok": False, "reason": f"Propuesta ya {p.status.value}."}
            p.status = ProposalStatus.APPROVED
            p.decided_at = now or datetime.now(p.created_at.tzinfo)
            await self._save(user_id, p)
            # Invariante: NO se ejecuta la orden. Se devuelve el handoff al usuario.
            return {"ok": True, "status": p.status.value, "handoff": p.execution_handoff()}
        except RedisError as e:
            logger.error(f"copy-trade approve redis error: {e}")
            return {"ok": False, "reason": _UNAVAILABLE}

    async def reject(self, user_id: str, proposal_id: str, now: Optional[datetime] = None) -> dict:
        try:
            p = await self._load(user_id, proposal_id)
            if p is None:
                return {"ok": False, "reason": "Propuesta no encontrada."}
            if p.status != ProposalStatus.PENDING:
                return {"ok": False, "reason": f"Propuesta ya {p.status.value}."}
            p.status = ProposalStatus.REJECTED
            p.decided_at = now or datetime.now(p.created_at.tzinfo)
            await self._save(user_id, p)
            return {"ok": True, "status": p.status.value}
        except RedisError as e:
            logger.error(f"copy-trade reject redis error: {e}")
            return {"ok": False, "reason": _UNAVAILABLE}

    async def get(self, user_id: str, proposal_id: str) -> Optional[dict]:
        try:
            p = await self._load(user_id, proposal_id)
            return p.to_dict() if p else None
        except RedisError as e:
            logger.error(f"copy-trade get redis error: {e}")
            return None
