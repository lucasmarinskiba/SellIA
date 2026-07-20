"""Affiliate Engine — Hotmart, Amazon, Mercado Libre, Beacons integration."""

from .affiliate_platform_analyzer import (
    HotmartAnalyzer,
    MercadoLibreAnalyzer,
    AmazonAnalyzer,
    BeaconsAnalyzer,
    AffiliateProductScore,
    PlatformComparator,
)
from .affiliate_sales_methods import (
    AFFILIATE_METHODS,
    get_methods_by_category,
    get_best_methods_for_product,
    get_fastest_methods,
)
from .affiliate_automation import (
    AffiliateAutomationOrchestrator,
    PlatformAutomationAdapter,
    AutomationTask,
)
from .affiliate_strategy_engine import AffiliateStrategyEngine, AffiliateStrategy
from .commission_tracker import CommissionTracker, AffiliateCommission, AffiliatePerformance

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
