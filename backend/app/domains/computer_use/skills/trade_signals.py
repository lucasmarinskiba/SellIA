"""Computer Use — Trade Signals & Copy-Trade Review (decision support).

Capa de soporte de decisión estilo "copy-trade" para operar mercados
financieros, cripto e inmobiliario internacionalmente a través de Computer
Use, PERO con un límite de seguridad estricto:

  * El agente ANALIZA y PROPONE operaciones (proposals): activo, lado,
    racional, riesgo, confianza, tamaño sugerido, stop/target.
  * El usuario debe estar ACTIVO (presencia/heartbeat) para que las
    propuestas se muestren; si no hay presencia, no se proponen operaciones.
  * El usuario ACEPTA o RECHAZA cada propuesta.
  * El agente NUNCA ejecuta la compra/venta ni mueve fondos ni ingresa
    credenciales: al aceptarse, entrega instrucciones para que el USUARIO
    ejecute la orden en su plataforma. (Política de seguridad SellIA y
    cumplimiento: no ejecutar transacciones financieras en nombre del
    usuario.)

Es una herramienta de soporte de decisión, no un motor de ejecución.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Dict, List, Optional


class AssetClass(str, Enum):
    CRYPTO = "crypto"
    EQUITY = "equity"
    FOREX = "forex"
    COMMODITY = "commodity"
    BOND = "bond"
    REAL_ESTATE = "real_estate"


class TradeSide(str, Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class AnalysisStyle(str, Enum):
    TECHNICAL = "technical"
    FUNDAMENTAL = "fundamental"
    QUANTITATIVE = "quantitative"
    SENTIMENT = "sentiment"
    MACRO = "macro"
    ON_CHAIN = "on_chain"
    MULTI_TIMEFRAME = "multi_timeframe"
    RELATIVE_VALUATION = "relative_valuation"
    RISK_MANAGEMENT = "risk_management"
    INCOME_APPROACH = "income_approach"        # inmobiliario (cap rate / NOI)
    COMPARABLE_APPROACH = "comparable_approach"  # inmobiliario (comps)
    COST_APPROACH = "cost_approach"            # inmobiliario (costo de reposición)


class RiskRating(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"


class ProposalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


# Estilos de análisis válidos por clase de activo (introspección + validación).
ANALYSIS_BY_ASSET: Dict[AssetClass, List[AnalysisStyle]] = {
    AssetClass.CRYPTO: [
        AnalysisStyle.TECHNICAL, AnalysisStyle.ON_CHAIN, AnalysisStyle.SENTIMENT,
        AnalysisStyle.MACRO, AnalysisStyle.MULTI_TIMEFRAME, AnalysisStyle.RISK_MANAGEMENT,
    ],
    AssetClass.EQUITY: [
        AnalysisStyle.FUNDAMENTAL, AnalysisStyle.TECHNICAL, AnalysisStyle.RELATIVE_VALUATION,
        AnalysisStyle.QUANTITATIVE, AnalysisStyle.SENTIMENT, AnalysisStyle.MACRO,
        AnalysisStyle.RISK_MANAGEMENT,
    ],
    AssetClass.FOREX: [
        AnalysisStyle.TECHNICAL, AnalysisStyle.MACRO, AnalysisStyle.MULTI_TIMEFRAME,
        AnalysisStyle.SENTIMENT, AnalysisStyle.RISK_MANAGEMENT,
    ],
    AssetClass.COMMODITY: [
        AnalysisStyle.MACRO, AnalysisStyle.TECHNICAL, AnalysisStyle.FUNDAMENTAL,
        AnalysisStyle.RISK_MANAGEMENT,
    ],
    AssetClass.BOND: [
        AnalysisStyle.MACRO, AnalysisStyle.FUNDAMENTAL, AnalysisStyle.RISK_MANAGEMENT,
    ],
    AssetClass.REAL_ESTATE: [
        AnalysisStyle.INCOME_APPROACH, AnalysisStyle.COMPARABLE_APPROACH,
        AnalysisStyle.COST_APPROACH, AnalysisStyle.MACRO, AnalysisStyle.RISK_MANAGEMENT,
    ],
}

# Ventana de presencia: el usuario debe haber dado señal de actividad dentro
# de este lapso para que se le presenten propuestas.
DEFAULT_PRESENCE_WINDOW_SEC = 120
# Vida de una propuesta antes de expirar (el mercado se mueve).
DEFAULT_PROPOSAL_TTL_SEC = 300


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class TradeProposal:
    """Propuesta de operación generada por el análisis del agente.

    NO es una orden. Requiere aprobación humana y ejecución por el usuario.
    """

    asset: str                       # ej. "BTC/USDT", "AAPL", "EUR/USD", "Depto Palermo"
    asset_class: AssetClass
    side: TradeSide
    rationale: str
    analysis_styles: List[AnalysisStyle]
    risk: RiskRating
    confidence: float                # 0.0–1.0
    market: str = ""                 # plataforma/mercado (ej. "Binance", "NYSE")
    suggested_allocation_pct: Optional[float] = None  # % del capital sugerido
    stop_loss: Optional[str] = None
    take_profit: Optional[str] = None
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    status: ProposalStatus = ProposalStatus.PENDING
    created_at: datetime = field(default_factory=_now)
    ttl_sec: int = DEFAULT_PROPOSAL_TTL_SEC
    decided_at: Optional[datetime] = None
    # Invariante de seguridad: el agente jamás ejecuta; el usuario ejecuta.
    requires_human_execution: bool = True

    def __post_init__(self) -> None:
        self.confidence = max(0.0, min(1.0, float(self.confidence)))
        if self.suggested_allocation_pct is not None:
            self.suggested_allocation_pct = max(0.0, min(100.0, float(self.suggested_allocation_pct)))
        valid = ANALYSIS_BY_ASSET.get(self.asset_class, [])
        if valid:
            self.analysis_styles = [s for s in self.analysis_styles if s in valid] or list(valid[:1])

    def is_expired(self, now: Optional[datetime] = None) -> bool:
        now = now or _now()
        return (now - self.created_at) > timedelta(seconds=self.ttl_sec)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "asset": self.asset,
            "asset_class": self.asset_class.value,
            "side": self.side.value,
            "market": self.market,
            "rationale": self.rationale,
            "analysis_styles": [s.value for s in self.analysis_styles],
            "risk": self.risk.value,
            "confidence": round(self.confidence, 3),
            "suggested_allocation_pct": self.suggested_allocation_pct,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "requires_human_execution": self.requires_human_execution,
        }

    def to_state(self) -> dict:
        """Serialización COMPLETA (incl. estado interno) para persistencia."""
        return {
            "asset": self.asset,
            "asset_class": self.asset_class.value,
            "side": self.side.value,
            "rationale": self.rationale,
            "analysis_styles": [s.value for s in self.analysis_styles],
            "risk": self.risk.value,
            "confidence": self.confidence,
            "market": self.market,
            "suggested_allocation_pct": self.suggested_allocation_pct,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "id": self.id,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "ttl_sec": self.ttl_sec,
            "decided_at": self.decided_at.isoformat() if self.decided_at else None,
            "requires_human_execution": self.requires_human_execution,
        }

    @classmethod
    def from_state(cls, d: dict) -> "TradeProposal":
        """Reconstruye una propuesta desde su estado persistido."""
        p = cls(
            asset=d["asset"],
            asset_class=AssetClass(d["asset_class"]),
            side=TradeSide(d["side"]),
            rationale=d["rationale"],
            analysis_styles=[AnalysisStyle(s) for s in d.get("analysis_styles", [])],
            risk=RiskRating(d["risk"]),
            confidence=d["confidence"],
            market=d.get("market", ""),
            suggested_allocation_pct=d.get("suggested_allocation_pct"),
            stop_loss=d.get("stop_loss"),
            take_profit=d.get("take_profit"),
            id=d["id"],
            ttl_sec=d.get("ttl_sec", DEFAULT_PROPOSAL_TTL_SEC),
            created_at=datetime.fromisoformat(d["created_at"]),
        )
        p.status = ProposalStatus(d.get("status", ProposalStatus.PENDING.value))
        decided = d.get("decided_at")
        p.decided_at = datetime.fromisoformat(decided) if decided else None
        p.requires_human_execution = d.get("requires_human_execution", True)
        return p

    def execution_handoff(self) -> dict:
        """Instrucciones para que el USUARIO ejecute la orden (el agente no la coloca)."""
        return {
            "proposal_id": self.id,
            "instruction": (
                f"Aprobado: {self.side.value.upper()} {self.asset} en {self.market or 'tu plataforma'}. "
                "El agente NO ejecuta la orden por seguridad. Realizá la operación vos mismo, "
                "respetando stop-loss y take-profit, y solo con capital que puedas arriesgar."
            ),
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "suggested_allocation_pct": self.suggested_allocation_pct,
            "agent_executes": False,
        }


class UserPresenceGate:
    """Exige presencia activa del usuario para mostrar propuestas.

    El frontend/cliente envía heartbeats mientras el usuario está al teclado
    o con SellIA abierto. Sin heartbeat reciente, no se proponen operaciones.
    """

    def __init__(self, window_sec: int = DEFAULT_PRESENCE_WINDOW_SEC):
        self.window_sec = window_sec
        self._last_heartbeat: Optional[datetime] = None

    def heartbeat(self, now: Optional[datetime] = None) -> None:
        self._last_heartbeat = now or _now()

    def is_active(self, now: Optional[datetime] = None) -> bool:
        if self._last_heartbeat is None:
            return False
        now = now or _now()
        return (now - self._last_heartbeat) <= timedelta(seconds=self.window_sec)


class CopyTradeReviewQueue:
    """Cola de propuestas pendientes de aprobación humana (estilo copy-trade).

    Reglas:
      * Solo emite/lista propuestas si el usuario está ACTIVO.
      * approve() marca aprobada y devuelve el handoff de ejecución para el
        usuario; NUNCA ejecuta la orden ni toca la plataforma.
      * reject() descarta la propuesta.
      * Las propuestas expiran por TTL.
    """

    def __init__(self, presence: Optional[UserPresenceGate] = None):
        self.presence = presence or UserPresenceGate()
        self._proposals: Dict[str, TradeProposal] = {}

    def submit(self, proposal: TradeProposal, now: Optional[datetime] = None) -> dict:
        """Encola una propuesta. Requiere usuario activo."""
        if not self.presence.is_active(now):
            return {
                "accepted": False,
                "reason": "Usuario inactivo: se requiere presencia activa para proponer operaciones.",
            }
        self._proposals[proposal.id] = proposal
        return {"accepted": True, "proposal": proposal.to_dict()}

    def _expire_stale(self, now: Optional[datetime] = None) -> None:
        now = now or _now()
        for p in self._proposals.values():
            if p.status == ProposalStatus.PENDING and p.is_expired(now):
                p.status = ProposalStatus.EXPIRED
                p.decided_at = now

    def pending(self, now: Optional[datetime] = None) -> List[dict]:
        self._expire_stale(now)
        if not self.presence.is_active(now):
            return []
        return [p.to_dict() for p in self._proposals.values() if p.status == ProposalStatus.PENDING]

    def approve(self, proposal_id: str, now: Optional[datetime] = None) -> dict:
        p = self._proposals.get(proposal_id)
        if p is None:
            return {"ok": False, "reason": "Propuesta no encontrada."}
        if not self.presence.is_active(now):
            return {"ok": False, "reason": "Usuario inactivo: no se puede aprobar sin presencia."}
        if p.is_expired(now):
            p.status = ProposalStatus.EXPIRED
            return {"ok": False, "reason": "Propuesta expirada; el mercado se movió."}
        if p.status != ProposalStatus.PENDING:
            return {"ok": False, "reason": f"Propuesta ya {p.status.value}."}
        p.status = ProposalStatus.APPROVED
        p.decided_at = now or _now()
        # Importante: NO se ejecuta la orden. Se devuelve el handoff al usuario.
        return {"ok": True, "status": p.status.value, "handoff": p.execution_handoff()}

    def reject(self, proposal_id: str, now: Optional[datetime] = None) -> dict:
        p = self._proposals.get(proposal_id)
        if p is None:
            return {"ok": False, "reason": "Propuesta no encontrada."}
        if p.status != ProposalStatus.PENDING:
            return {"ok": False, "reason": f"Propuesta ya {p.status.value}."}
        p.status = ProposalStatus.REJECTED
        p.decided_at = now or _now()
        return {"ok": True, "status": p.status.value}

    def get(self, proposal_id: str) -> Optional[dict]:
        p = self._proposals.get(proposal_id)
        return p.to_dict() if p else None
