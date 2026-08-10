"""Phase 24: Adaptive Backend Architecture - personalizes responses per user."""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class UserSegment(str, Enum):
    ULTRA_EARLY = "ultra_early"  # 0-3 days
    EARLY = "early"  # 3-14 days
    ACTIVE = "active"  # 14+ days, has leads
    CONVERTER = "converter"  # Has closed deals
    POWER_USER = "power_user"  # 10+ deals
    DORMANT = "dormant"  # Inactive 7+ days


class UserNeed(str, Enum):
    LEAD_GENERATION = "lead_generation"
    CONVERSION = "conversion"
    SCALING = "scaling"
    OPTIMIZATION = "optimization"
    RETENTION = "retention"


@dataclass
class UserContext:
    user_id: str
    segment: UserSegment
    primary_need: UserNeed
    engagement_score: float  # 0-1
    urgency: str  # low, medium, high, critical
    preferred_content_type: str  # video, text, demo, data
    language: str = "es"
    timezone: str = "Europe/Madrid"


@dataclass
class AdaptiveResponse:
    endpoint_name: str
    personalized: bool
    content_type: str
    urgency_level: str
    recommended_next_action: str
    metrics: Dict[str, Any] = field(default_factory=dict)


class AdaptiveEngine:
    """Backend that adapts responses based on user profile"""

    def __init__(self):
        self.user_profiles: Dict[str, UserContext] = {}
        self.segment_configs = self._build_segment_configs()

    def analyze_user(self, user_id: str, business_metrics: Dict[str, Any]) -> UserContext:
        """Analyze user and determine segment + needs"""

        days_active = business_metrics.get("days_in_business", 0)
        leads = business_metrics.get("leads_generated", 0)
        deals = business_metrics.get("deals_closed", 0)
        last_activity_hours = business_metrics.get("hours_since_last_activity", 999)

        # Determine segment
        if days_active < 1:
            segment = UserSegment.ULTRA_EARLY
        elif days_active < 14:
            segment = UserSegment.EARLY
        elif deals >= 10:
            segment = UserSegment.POWER_USER
        elif deals > 0:
            segment = UserSegment.CONVERTER
        elif leads > 0:
            segment = UserSegment.ACTIVE
        elif last_activity_hours > 168:  # 7 days
            segment = UserSegment.DORMANT
        else:
            segment = UserSegment.EARLY

        # Determine primary need
        if deals == 0 and days_active < 7:
            primary_need = UserNeed.LEAD_GENERATION
        elif leads > 0 and deals == 0:
            primary_need = UserNeed.CONVERSION
        elif deals >= 5 and deals < 50:
            primary_need = UserNeed.SCALING
        elif deals >= 50:
            primary_need = UserNeed.OPTIMIZATION
        elif last_activity_hours > 168:
            primary_need = UserNeed.RETENTION
        else:
            primary_need = UserNeed.LEAD_GENERATION

        # Calculate engagement
        engagement_score = min(1.0, (deals * 0.3 + leads * 0.1) / 10 + (0.5 if last_activity_hours < 24 else 0))

        # Determine urgency
        if segment == UserSegment.ULTRA_EARLY:
            urgency = "critical"
        elif segment == UserSegment.DORMANT:
            urgency = "high"
        elif days_active < 14 and deals == 0:
            urgency = "high"
        elif segment == UserSegment.EARLY:
            urgency = "medium"
        else:
            urgency = "low"

        context = UserContext(
            user_id=user_id,
            segment=segment,
            primary_need=primary_need,
            engagement_score=engagement_score,
            urgency=urgency,
            preferred_content_type=self._detect_content_preference(segment)
        )

        self.user_profiles[user_id] = context
        logger.info(f"User analyzed: {user_id} - Segment: {segment.value}, Need: {primary_need.value}")

        return context

    def _detect_content_preference(self, segment: UserSegment) -> str:
        """Detect preferred content type by segment"""
        preferences = {
            UserSegment.ULTRA_EARLY: "video",  # Quick onboarding
            UserSegment.EARLY: "text",  # Actionable guides
            UserSegment.ACTIVE: "data",  # Analytics/metrics
            UserSegment.CONVERTER: "data",  # Performance tracking
            UserSegment.POWER_USER: "demo",  # Advanced features
            UserSegment.DORMANT: "video",  # Re-engagement
        }
        return preferences.get(segment, "text")

    def _build_segment_configs(self) -> Dict[str, Dict[str, Any]]:
        """Build configs for each segment"""
        return {
            UserSegment.ULTRA_EARLY.value: {
                "features": ["onboarding", "first_lead_gen", "quick_demo"],
                "messaging": "action-oriented",
                "frequency": "daily",
                "complexity": "low"
            },
            UserSegment.EARLY.value: {
                "features": ["lead_gen", "conversion_tips", "pricing_guide"],
                "messaging": "encouraging",
                "frequency": "daily",
                "complexity": "medium"
            },
            UserSegment.ACTIVE.value: {
                "features": ["analytics", "ab_testing", "optimization"],
                "messaging": "data-driven",
                "frequency": "3x/week",
                "complexity": "high"
            },
            UserSegment.CONVERTER.value: {
                "features": ["scaling", "team_building", "expansion"],
                "messaging": "strategic",
                "frequency": "weekly",
                "complexity": "high"
            },
            UserSegment.POWER_USER.value: {
                "features": ["enterprise", "integrations", "automation"],
                "messaging": "partnership",
                "frequency": "as-needed",
                "complexity": "very-high"
            },
            UserSegment.DORMANT.value: {
                "features": ["re_engagement", "updates", "success_stories"],
                "messaging": "motivational",
                "frequency": "weekly",
                "complexity": "low"
            }
        }

    def adapt_endpoint_response(
        self, user_id: str, endpoint_name: str, base_response: Dict[str, Any]
    ) -> AdaptiveResponse:
        """Adapt endpoint response based on user context"""

        if user_id not in self.user_profiles:
            return AdaptiveResponse(
                endpoint_name=endpoint_name,
                personalized=False,
                content_type="text",
                urgency_level="medium",
                recommended_next_action="Complete profile"
            )

        context = self.user_profiles[user_id]
        config = self.segment_configs.get(context.segment.value, {})

        # Adapt content based on segment
        adapted = self._adapt_by_segment(context, endpoint_name, base_response)

        return AdaptiveResponse(
            endpoint_name=endpoint_name,
            personalized=True,
            content_type=context.preferred_content_type,
            urgency_level=context.urgency,
            recommended_next_action=self._get_recommended_action(context),
            metrics={
                "segment": context.segment.value,
                "engagement_score": context.engagement_score,
                "primary_need": context.primary_need.value
            }
        )

    def _adapt_by_segment(
        self, context: UserContext, endpoint: str, response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Adapt response content by user segment"""

        if context.segment == UserSegment.ULTRA_EARLY:
            return self._simplify_for_beginner(response)
        elif context.segment == UserSegment.POWER_USER:
            return self._enrich_for_power_user(response)
        elif context.segment == UserSegment.DORMANT:
            return self._motivate_dormant_user(response)
        else:
            return response

    def _simplify_for_beginner(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Simplify response for beginners"""
        # Remove advanced metrics, focus on actions
        return {
            **response,
            "simplified": True,
            "focus": "action_items"
        }

    def _enrich_for_power_user(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich response for power users"""
        # Add advanced analytics, API details
        return {
            **response,
            "advanced": True,
            "api_available": True,
            "webhooks": True,
            "batch_operations": True
        }

    def _motivate_dormant_user(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Add motivation for dormant users"""
        return {
            **response,
            "re_engagement_message": "We've improved! Check out new features.",
            "incentive": "comeback_bonus"
        }

    def _get_recommended_action(self, context: UserContext) -> str:
        """Get recommended next action for user"""

        recommendations = {
            (UserSegment.ULTRA_EARLY, UserNeed.LEAD_GENERATION): "Start your first campaign now",
            (UserSegment.EARLY, UserNeed.LEAD_GENERATION): "Generate 10 leads today",
            (UserSegment.EARLY, UserNeed.CONVERSION): "Follow up with your leads",
            (UserSegment.ACTIVE, UserNeed.CONVERSION): "Close your first deal",
            (UserSegment.CONVERTER, UserNeed.SCALING): "Hire your first team member",
            (UserSegment.POWER_USER, UserNeed.OPTIMIZATION): "Explore API integrations",
            (UserSegment.DORMANT, UserNeed.RETENTION): "Come back - we've improved!",
        }

        return recommendations.get(
            (context.segment, context.primary_need),
            "Continue with your goals"
        )

    def get_personalization_summary(self, user_id: str) -> Dict[str, Any]:
        """Get full personalization summary"""

        if user_id not in self.user_profiles:
            return {}

        context = self.user_profiles[user_id]
        config = self.segment_configs.get(context.segment.value, {})

        return {
            "user_id": user_id,
            "segment": context.segment.value,
            "primary_need": context.primary_need.value,
            "engagement_score": context.engagement_score,
            "urgency": context.urgency,
            "recommended_features": config.get("features", []),
            "messaging_style": config.get("messaging", ""),
            "content_frequency": config.get("frequency", ""),
            "recommended_action": self._get_recommended_action(context)
        }
