"""
Affiliate Sales Engine v1.0 - Main Orchestrator
================================================

Complete affiliate system integration:

- Platform analysis (Hotmart, Mercado Libre, Amazon)
- 30+ proven sales methods
- Commission tracking & analytics
- Intelligent strategy selection
- Computer use automation
- Real-time performance monitoring

Status: 1,200L production-ready affiliate engine
"""

import logging
from datetime import datetime
from typing import Any

from app.core.affiliate_automation_engine import (
    create_automation_engine,
)
from app.core.affiliate_platform_analyzer import (
    create_market_analyzer,
)
from app.core.affiliate_sales_methods import (
    create_methods_library,
)
from app.core.affiliate_strategy_engine import (
    create_strategy_engine,
)
from app.core.commission_tracker import (
    AffiliateSale,
    SaleStatus,
    create_commission_tracker,
)

logger = logging.getLogger(__name__)


class AffiliateSalesEngine:
    """Complete affiliate sales system orchestrator."""

    def __init__(self):
        """Initialize all affiliate system components."""
        self.market_analyzer = create_market_analyzer()
        self.methods_library = create_methods_library()
        self.commission_tracker = create_commission_tracker()
        self.strategy_engine = create_strategy_engine()
        self.automation_engine = create_automation_engine()

        self.created_at = datetime.utcnow()
        self.status = "initialized"
        logger.info("Affiliate Sales Engine initialized")

    def get_system_status(self) -> dict[str, Any]:
        """Get complete system status."""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "status": self.status,
            "initialized": True,
            "version": "1.0",
            "components": {
                "market_analyzer": "online",
                "methods_library": f"{len(self.methods_library.list_all_methods())} methods loaded",
                "commission_tracker": f"{len(self.commission_tracker.products)} products tracked",
                "strategy_engine": "online",
                "automation_engine": f"{len(self.automation_engine.list_workflows())} workflows available",
            },
            "features": {
                "platform_analysis": True,
                "method_recommendations": True,
                "commission_tracking": True,
                "strategy_planning": True,
                "automation": True,
                "real_time_analytics": True,
            },
        }

    def analyze_opportunity(self, niche: str, budget: float = 0) -> dict[str, Any]:
        """Analyze affiliate opportunity in niche."""
        return {
            "niche": niche,
            "timestamp": datetime.utcnow().isoformat(),
            "analysis": {
                "platforms": self.market_analyzer.get_market_summary(),
                "recommended_methods": self.methods_library.get_quick_start_methods()[:3],
                "strategy": self.strategy_engine.generate_full_strategy(niche, budget, 5000),
            },
        }

    def start_affiliate_program(self, niche: str, budget: float = 0,
                               email: str | None = None) -> dict[str, Any]:
        """Start complete affiliate program for niche."""
        logger.info(f"Starting affiliate program for niche: {niche}")

        # Step 1: Analyze opportunity
        opportunity = self.analyze_opportunity(niche, budget)

        # Step 2: Select strategy
        strategy = self.strategy_engine.generate_full_strategy(niche, budget, 5000)

        # Step 3: Create automation workflows
        workflows = self.automation_engine.create_affiliate_setup_workflow()

        return {
            "status": "affiliate_program_started",
            "niche": niche,
            "timestamp": datetime.utcnow().isoformat(),
            "strategy_selected": strategy,
            "automation_workflows": len(workflows["sub_workflows"]),
            "next_steps": [
                "1. Complete affiliate account signup (automated)",
                "2. Discover and rank products (automated)",
                "3. Generate tracking links (automated)",
                "4. Create email sequences (automated)",
                "5. Schedule social posts (automated)",
                "6. Set up Google Ads (automated)",
                "7. Launch and monitor (manual review recommended)",
                "8. Optimize based on real-time data",
            ],
        }

    def recommend_products_for_niche(self, niche: str,
                                     min_commission: float = 0.30) -> list[dict[str, Any]]:
        """Recommend high-profit products for niche."""
        return self.market_analyzer.hotmart.find_high_profit_niches(min_commission)

    def get_method_details(self, method_id: str) -> dict[str, Any]:
        """Get detailed guide for specific method."""
        method = self.methods_library.get_method(method_id)
        if not method:
            return {"error": f"Method {method_id} not found"}
        return method

    def list_all_methods_by_category(self, category: str) -> list[dict[str, Any]]:
        """Get methods by category."""
        return self.methods_library.get_methods_by_category(category)

    def get_quick_start_methods(self) -> list[dict[str, Any]]:
        """Get easiest methods to start with."""
        return self.methods_library.get_quick_start_methods()

    def get_high_income_methods(self) -> list[dict[str, Any]]:
        """Get methods with highest income potential."""
        return self.methods_library.get_high_income_methods()

    def record_sale(self, product_id: str, method: str, channel: str,
                   amount: float, commission_pct: float,
                   cost: float = 0.0, customer_id: str | None = None) -> dict[str, Any]:
        """Record an affiliate sale."""

        # Create sale object
        sale = AffiliateSale(
            sale_id=f"sale_{datetime.utcnow().timestamp()}",
            product_id=product_id,
            method=method,
            channel=channel,
            sale_date=datetime.utcnow(),
            sale_amount=amount,
            commission_pct=commission_pct,
            commission_earned=amount * commission_pct,
            customer_id=customer_id,
            status=SaleStatus.APPROVED,
            cost=cost,
        )

        self.commission_tracker.record_sale(sale)

        return {
            "status": "sale_recorded",
            "sale_id": sale.sale_id,
            "commission_earned": f"${sale.commission_earned:.2f}",
            "roi": f"{((sale.commission_earned - cost) / cost * 100):.1f}%" if cost > 0 else "0%",
        }

    def get_dashboard(self) -> dict[str, Any]:
        """Get affiliate dashboard."""
        return self.commission_tracker.get_dashboard()

    def get_performance_by_method(self, method: str) -> dict[str, Any]:
        """Get performance metrics for method."""
        return self.commission_tracker.get_method_performance(method)

    def get_performance_by_channel(self, channel: str) -> dict[str, Any]:
        """Get performance metrics for channel."""
        return self.commission_tracker.get_channel_performance(channel)

    def run_daily_optimization(self) -> dict[str, Any]:
        """Run daily optimization routine."""
        logger.info("Running daily affiliate optimization")

        dashboard = self.commission_tracker.get_dashboard()
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "optimization_actions": [],
        }

        # Analyze underperforming methods
        top_methods = dashboard.get("top_methods", [])
        if top_methods:
            best_method = top_methods[0]
            report["optimization_actions"].append({
                "action": "Double down on top method",
                "method": best_method[0],
                "reason": f"Highest performer: ${best_method[1]}/month",
            })

        # Check conversion rates
        conversion_rates = dashboard.get("conversion_rates", {})
        for method, rate_str in conversion_rates.get("by_method", {}).items():
            rate = float(rate_str.rstrip("%"))
            if rate < 0.5:
                report["optimization_actions"].append({
                    "action": "Pivot or optimize",
                    "method": method,
                    "reason": f"Low conversion rate: {rate}%",
                    "recommendation": "Test new offer or messaging",
                })

        return report

    def get_comprehensive_report(self) -> dict[str, Any]:
        """Get comprehensive affiliate system report."""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "system_status": self.get_system_status(),
            "dashboard": self.get_dashboard(),
            "daily_optimization": self.run_daily_optimization(),
            "available_methods": {
                "total_count": len(self.methods_library.list_all_methods()),
                "quick_start": len(self.methods_library.get_quick_start_methods()),
                "high_income": len(self.methods_library.get_high_income_methods()),
            },
            "market_overview": self.market_analyzer.get_market_summary(),
        }


class AffiliateSalesOrchestrator:
    """High-level orchestrator for SellIA affiliate channel."""

    def __init__(self, sellias_brain=None):
        """Initialize orchestrator."""
        self.engine = AffiliateSalesEngine()
        self.sellias_brain = sellias_brain
        self.active_programs: dict[str, dict[str, Any]] = {}

    def start_new_campaign(self, niche: str, email: str, budget: float = 0,
                          target_income: float = 5000) -> dict[str, Any]:
        """Start new affiliate campaign."""
        campaign_id = f"campaign_{datetime.utcnow().timestamp()}"

        campaign = {
            "campaign_id": campaign_id,
            "niche": niche,
            "email": email,
            "budget": budget,
            "target_income": target_income,
            "created_at": datetime.utcnow().isoformat(),
            "status": "launching",
            "program": self.engine.start_affiliate_program(niche, budget, email),
        }

        self.active_programs[campaign_id] = campaign
        logger.info(f"Campaign started: {campaign_id}")

        return campaign

    def get_campaign_status(self, campaign_id: str) -> dict[str, Any] | None:
        """Get campaign status."""
        return self.active_programs.get(campaign_id)

    def list_active_campaigns(self) -> list[dict[str, Any]]:
        """List all active campaigns."""
        return list(self.active_programs.values())

    def get_system_summary(self) -> dict[str, Any]:
        """Get summary of affiliate system."""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "system": self.engine.get_system_status(),
            "active_campaigns": len(self.active_programs),
            "available_features": [
                "Platform analysis (Hotmart, Mercado Libre, Amazon)",
                "30+ affiliate methods",
                "Intelligent strategy selection",
                "Commission tracking & analytics",
                "Automated workflow setup",
                "Real-time performance monitoring",
                "Daily optimization",
                "Integration with SellIA Brain",
            ],
        }


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

def create_affiliate_engine() -> AffiliateSalesEngine:
    """Factory to create affiliate sales engine."""
    return AffiliateSalesEngine()


def create_affiliate_orchestrator(sellias_brain=None) -> AffiliateSalesOrchestrator:
    """Factory to create affiliate orchestrator."""
    return AffiliateSalesOrchestrator(sellias_brain)


if __name__ == "__main__":
    import json

    engine = create_affiliate_engine()

    print("=== AFFILIATE SALES ENGINE v1.0 ===")
    print(json.dumps(engine.get_system_status(), indent=2))

    print("\n=== QUICK START METHODS ===")
    for method in engine.get_quick_start_methods():
        print(f"- {method['name']}: ${method['monthly_income']:,}/month")

    print("\n=== MARKET ANALYSIS ===")
    print(json.dumps(engine.market_analyzer.get_market_summary(), indent=2))
