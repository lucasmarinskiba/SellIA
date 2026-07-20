"""Computer Use — Skills & Knowledge layer.

Da al agente conocimiento de dominio (estrategias de venta, creación de
contenido, redes sociales, ads, plataformas de venta) y políticas de
ejecución para los modos *supervisado* y *piloto automático*.
"""

from .knowledge_base import (
    SKILL_DOMAINS,
    SALES_TEAM_ROLES,
    SkillDomain,
    detect_skill_domains,
    build_skill_brief,
    list_platform_skills,
    list_sales_team_roles,
)
from .autopilot_policy import (
    AutopilotMode,
    RiskLevel,
    PolicyDecision,
    AutopilotPolicy,
    classify_action_risk,
)
from .trade_signals import (
    AssetClass,
    TradeSide,
    AnalysisStyle,
    RiskRating,
    ProposalStatus,
    ANALYSIS_BY_ASSET,
    TradeProposal,
    UserPresenceGate,
    CopyTradeReviewQueue,
)
from .trade_store import RedisCopyTradeStore

__all__ = [
    "SKILL_DOMAINS",
    "SALES_TEAM_ROLES",
    "SkillDomain",
    "detect_skill_domains",
    "build_skill_brief",
    "list_platform_skills",
    "list_sales_team_roles",
    "AutopilotMode",
    "RiskLevel",
    "PolicyDecision",
    "AutopilotPolicy",
    "classify_action_risk",
    "AssetClass",
    "TradeSide",
    "AnalysisStyle",
    "RiskRating",
    "ProposalStatus",
    "ANALYSIS_BY_ASSET",
    "TradeProposal",
    "UserPresenceGate",
    "CopyTradeReviewQueue",
    "RedisCopyTradeStore",
]
