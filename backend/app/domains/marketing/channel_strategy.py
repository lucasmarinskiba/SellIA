"""Phase 13: Channel-specific marketing strategies."""

from dataclasses import dataclass, field
from typing import List, Dict, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ChannelPriority(str, Enum):
    PRIORITY_1 = "priority_1"
    PRIORITY_2 = "priority_2"
    PRIORITY_3 = "priority_3"
    SECONDARY = "secondary"


@dataclass
class ChannelAction:
    action: str
    description: str
    effort_level: str  # low, medium, high
    timeline_days: int
    expected_leads_per_month: int
    cost_estimate: str  # free, low, medium, high


@dataclass
class ChannelPlan:
    channel: str
    priority: ChannelPriority
    actions: List[ChannelAction] = field(default_factory=list)
    expected_leads_per_month: int = 0
    estimated_conversion_rate: float = 0.2
    budget_recommendation: str = ""
    timeline_to_first_lead_days: int = 7
    quick_wins: List[str] = field(default_factory=list)


@dataclass
class ChannelStrategy:
    business_model: str
    channels: List[ChannelPlan] = field(default_factory=list)
    total_expected_leads_per_month: int = 0
    estimated_monthly_cost: int = 0
    priority_order: List[str] = field(default_factory=list)
    phased_approach: List[Dict[str, Any]] = field(default_factory=list)


class ChannelStrategyGenerator:
    """Generate marketing strategies by channel"""

    def generate_strategy(self, business_model: str) -> ChannelStrategy:
        """Generate channel-specific strategy"""

        logger.info(f"Generating channel strategy for {business_model}")

        if business_model == "physical_store":
            return self._strategy_physical_store()
        elif business_model == "online_only":
            return self._strategy_online()
        elif business_model == "service_at_home":
            return self._strategy_service()
        elif business_model == "b2b_consulting":
            return self._strategy_b2b()
        else:
            return self._strategy_generic()

    def _strategy_physical_store(self) -> ChannelStrategy:
        """Strategy for physical retail stores"""

        channels = [
            ChannelPlan(
                channel="google_maps",
                priority=ChannelPriority.PRIORITY_1,
                actions=[
                    ChannelAction(
                        action="Optimize GMB Profile",
                        description="Complete profile, add photos, add hours, add categories",
                        effort_level="low",
                        timeline_days=2,
                        expected_leads_per_month=15,
                        cost_estimate="free"
                    ),
                    ChannelAction(
                        action="Collect Reviews",
                        description="Systematically ask customers for reviews",
                        effort_level="medium",
                        timeline_days=30,
                        expected_leads_per_month=10,
                        cost_estimate="free"
                    ),
                    ChannelAction(
                        action="Regular Posts",
                        description="Post 2x/week: deals, hours, announcements",
                        effort_level="low",
                        timeline_days=1,
                        expected_leads_per_month=8,
                        cost_estimate="free"
                    )
                ],
                expected_leads_per_month=33,
                quick_wins=[
                    "Add 10 photos of store + products today",
                    "Ask 5 happy customers for reviews today",
                    "Setup response template for reviews"
                ]
            ),
            ChannelPlan(
                channel="instagram",
                priority=ChannelPriority.PRIORITY_2,
                actions=[
                    ChannelAction(
                        action="Content Calendar",
                        description="Plan 30 days of content (daily posts + reels)",
                        effort_level="medium",
                        timeline_days=1,
                        expected_leads_per_month=8,
                        cost_estimate="free"
                    ),
                    ChannelAction(
                        action="Visual Storytelling",
                        description="Behind-the-scenes + product showcase",
                        effort_level="medium",
                        timeline_days=1,
                        expected_leads_per_month=6,
                        cost_estimate="free"
                    ),
                    ChannelAction(
                        action="Engagement",
                        description="Reply to comments, interact with followers",
                        effort_level="low",
                        timeline_days=1,
                        expected_leads_per_month=4,
                        cost_estimate="free"
                    )
                ],
                expected_leads_per_month=18,
                quick_wins=[
                    "Post best 5 product photos today",
                    "Follow 50 local businesses",
                    "Setup Instagram Insights"
                ]
            ),
            ChannelPlan(
                channel="whatsapp",
                priority=ChannelPriority.PRIORITY_3,
                actions=[
                    ChannelAction(
                        action="WhatsApp Business Setup",
                        description="Enable auto-replies, business info, quick responses",
                        effort_level="low",
                        timeline_days=1,
                        expected_leads_per_month=5,
                        cost_estimate="free"
                    )
                ],
                expected_leads_per_month=5,
                quick_wins=["Setup WhatsApp Business profile today"]
            )
        ]

        return ChannelStrategy(
            business_model="physical_store",
            channels=channels,
            total_expected_leads_per_month=56,
            estimated_monthly_cost=0,
            priority_order=["google_maps", "instagram", "whatsapp"],
            phased_approach=[
                {
                    "phase": 1,
                    "duration_days": 7,
                    "focus": "Google Maps optimization",
                    "expected_leads": 10
                },
                {
                    "phase": 2,
                    "duration_days": 14,
                    "focus": "Instagram content calendar",
                    "expected_leads": 15
                },
                {
                    "phase": 3,
                    "duration_days": 7,
                    "focus": "WhatsApp automation",
                    "expected_leads": 20
                }
            ]
        )

    def _strategy_online(self) -> ChannelStrategy:
        """Strategy for online-only businesses"""

        channels = [
            ChannelPlan(
                channel="google_search",
                priority=ChannelPriority.PRIORITY_1,
                actions=[
                    ChannelAction(
                        action="SEO Optimization",
                        description="Target 20 high-intent keywords",
                        effort_level="high",
                        timeline_days=30,
                        expected_leads_per_month=25,
                        cost_estimate="free"
                    ),
                    ChannelAction(
                        action="Content Strategy",
                        description="Blog posts, guides, FAQs",
                        effort_level="high",
                        timeline_days=30,
                        expected_leads_per_month=15,
                        cost_estimate="free"
                    )
                ],
                expected_leads_per_month=40
            ),
            ChannelPlan(
                channel="google_ads",
                priority=ChannelPriority.PRIORITY_2,
                actions=[
                    ChannelAction(
                        action="Search Campaigns",
                        description="High-intent keywords bidding",
                        effort_level="medium",
                        timeline_days=3,
                        expected_leads_per_month=30,
                        cost_estimate="medium"
                    )
                ],
                expected_leads_per_month=30,
                budget_recommendation="$300-500/month"
            )
        ]

        return ChannelStrategy(
            business_model="online_only",
            channels=channels,
            total_expected_leads_per_month=70
        )

    def _strategy_service(self) -> ChannelStrategy:
        """Strategy for at-home services"""

        channels = [
            ChannelPlan(
                channel="google_maps",
                priority=ChannelPriority.PRIORITY_1,
                expected_leads_per_month=20
            ),
            ChannelPlan(
                channel="google_search",
                priority=ChannelPriority.PRIORITY_2,
                expected_leads_per_month=15
            ),
            ChannelPlan(
                channel="whatsapp",
                priority=ChannelPriority.PRIORITY_3,
                expected_leads_per_month=10
            )
        ]

        return ChannelStrategy(
            business_model="service_at_home",
            channels=channels,
            total_expected_leads_per_month=45
        )

    def _strategy_b2b(self) -> ChannelStrategy:
        """Strategy for B2B consulting"""

        channels = [
            ChannelPlan(
                channel="linkedin",
                priority=ChannelPriority.PRIORITY_1,
                expected_leads_per_month=20
            ),
            ChannelPlan(
                channel="email",
                priority=ChannelPriority.PRIORITY_2,
                expected_leads_per_month=15
            ),
            ChannelPlan(
                channel="content_marketing",
                priority=ChannelPriority.PRIORITY_3,
                expected_leads_per_month=10
            )
        ]

        return ChannelStrategy(
            business_model="b2b_consulting",
            channels=channels,
            total_expected_leads_per_month=45
        )

    def _strategy_generic(self) -> ChannelStrategy:
        """Generic strategy"""

        channels = [
            ChannelPlan(
                channel="google_search",
                priority=ChannelPriority.PRIORITY_1,
                expected_leads_per_month=20
            )
        ]

        return ChannelStrategy(
            business_model="generic",
            channels=channels,
            total_expected_leads_per_month=20
        )
