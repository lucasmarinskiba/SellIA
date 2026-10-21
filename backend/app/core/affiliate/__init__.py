"""Affiliate Engine — Hotmart, Amazon, Mercado Libre, Beacons integration."""

from .affiliate_automation import (
    AffiliateAutomationOrchestrator,
    AutomationTask,
    PlatformAutomationAdapter,
)
from .affiliate_platform_analyzer import (
    AffiliateProductScore,
    AmazonAnalyzer,
    BeaconsAnalyzer,
    HotmartAnalyzer,
    MercadoLibreAnalyzer,
    PlatformComparator,
)
from .affiliate_sales_methods import (
    AFFILIATE_METHODS,
    get_best_methods_for_product,
    get_fastest_methods,
    get_methods_by_category,
)
from .affiliate_strategy_engine import AffiliateStrategy, AffiliateStrategyEngine
from .commission_tracker import (
    AffiliateCommission,
    AffiliatePerformance,
    CommissionTracker,
)

__all__ = [
    # Platform analyzers
    "HotmartAnalyzer",
    "MercadoLibreAnalyzer",
    "AmazonAnalyzer",
    "BeaconsAnalyzer",
    "AffiliateProductScore",
    "PlatformComparator",
    # Sales methods
    "AFFILIATE_METHODS",
    "get_methods_by_category",
    "get_best_methods_for_product",
    "get_fastest_methods",
    # Automation
    "AffiliateAutomationOrchestrator",
    "PlatformAutomationAdapter",
    "AutomationTask",
    # Strategy
    "AffiliateStrategyEngine",
    "AffiliateStrategy",
    # Tracking
    "CommissionTracker",
    "AffiliateCommission",
    "AffiliatePerformance",
]
