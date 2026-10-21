"""Computer Use — Skills & Knowledge layer.

Da al agente conocimiento de dominio (estrategias de venta, creación de
contenido, redes sociales, ads, plataformas de venta) y políticas de
ejecución para los modos *supervisado* y *piloto automático*.
"""

from .autopilot_policy import (
    AutopilotMode,
    AutopilotPolicy,
    PolicyDecision,
    RiskLevel,
    classify_action_risk,
)
from .knowledge_base import (
    SALES_TEAM_ROLES,
    SKILL_DOMAINS,
    SkillDomain,
    build_skill_brief,
    detect_skill_domains,
    list_platform_skills,
    list_sales_team_roles,
)
from .trade_signals import (
    ANALYSIS_BY_ASSET,
    AnalysisStyle,
    AssetClass,
    CopyTradeReviewQueue,
    ProposalStatus,
    RiskRating,
    TradeProposal,
    TradeSide,
    UserPresenceGate,
)
from .trade_store import RedisCopyTradeStore

__all__ = [
    "ANALYSIS_BY_ASSET",
    "SALES_TEAM_ROLES",
    "SKILL_DOMAINS",
    "AnalysisStyle",
    "AssetClass",
    "AutopilotMode",
    "AutopilotPolicy",
    "CopyTradeReviewQueue",
    "PolicyDecision",
    "ProposalStatus",
    "RedisCopyTradeStore",
    "RiskLevel",
    "RiskRating",
    "SkillDomain",
    "TradeProposal",
    "TradeSide",
    "UserPresenceGate",
    "build_skill_brief",
    "classify_action_risk",
    "detect_skill_domains",
    "list_platform_skills",
    "list_sales_team_roles",
]
