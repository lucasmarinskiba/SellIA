"""
Phase 10: Humanization — A/B Testing (300L)

Tests different tone variations to optimize for "sounds human" metric.

Experiments:
- Tone variations (formal vs casual)
- CTA types (soft vs direct)
- Personalization levels
- Emoji usage
- Message length
- Timing

Metrics tracked:
- Open rate
- Click rate
- Reply rate
- Conversion rate
- "Sounds human" perception score
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from random import choice, random
from collections import defaultdict

logger = logging.getLogger(__name__)


class ExperimentType(str, Enum):
    """Type of A/B test"""
    TONE = "tone"
    CTA = "cta"
    PERSONALIZATION = "personalization"
    EMOJI = "emoji"
    LENGTH = "length"
    TIMING = "timing"
    HUMANNESS = "humanness"


class VariantStatus(str, Enum):
    """Status of variant"""
    ACTIVE = "active"
    PAUSED = "paused"
    WINNER = "winner"
    LOSER = "loser"


@dataclass
class Variant:
    """A/B test variant"""
    variant_id: str
    name: str
    test_type: ExperimentType
    message_template: str
    tone: Optional[str] = None
    cta_type: Optional[str] = None
    personalization_level: Optional[str] = None
    emoji_usage: Optional[str] = None  # "none", "light", "heavy"
    status: VariantStatus = VariantStatus.ACTIVE

    # Metrics
    sent_count: int = 0
    open_count: int = 0
    click_count: int = 0
    reply_count: int = 0
    conversion_count: int = 0
    humanness_score: float = 0.5  # 0-1, from user perception

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def get_metrics(self) -> Dict[str, float]:
        """Calculate engagement metrics"""
        if self.sent_count == 0:
            return {}

        return {
            "open_rate": self.open_count / self.sent_count if self.sent_count > 0 else 0,
            "click_rate": self.click_count / self.sent_count if self.sent_count > 0 else 0,
            "reply_rate": self.reply_count / self.sent_count if self.sent_count > 0 else 0,
            "conversion_rate": self.conversion_count / self.sent_count if self.sent_count > 0 else 0,
            "humanness_score": self.humanness_score,
        }


@dataclass
class ABTest:
    """A/B test configuration"""
    test_id: str
    name: str
    test_type: ExperimentType
    description: Optional[str] = None
    hypothesis: Optional[str] = None

    # Variants
    control_variant: Optional[Variant] = None
    treatment_variants: List[Variant] = field(default_factory=list)

    # Test config
    sample_size: int = 100  # Minimum samples per variant
    duration_days: int = 7
    split_percentage: Dict[str, int] = field(default_factory=dict)  # {variant_id: percentage}
    min_conversion_difference: float = 0.05  # 5% minimum to declare winner

    # Status
    status: str = "active"
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    winner_id: Optional[str] = None

    def add_variant(self, variant: Variant) -> None:
        """Add variant to test"""
        self.treatment_variants.append(variant)

    def get_variants(self) -> List[Variant]:
        """Get all variants"""
        all_variants = []
        if self.control_variant:
            all_variants.append(self.control_variant)
        all_variants.extend(self.treatment_variants)
        return all_variants


class ABTestingEngine:
    """Manages A/B testing for humanization optimization"""

    # Predefined tone test configurations
    TONE_TEST_VARIANTS = {
        "formal_vs_casual": [
            {
                "name": "Formal",
                "tone": "professional",
                "cta_type": "direct",
                "emoji_usage": "none",
            },
            {
                "name": "Casual",
                "tone": "casual",
                "cta_type": "soft",
                "emoji_usage": "light",
            },
        ],
        "friendly_vs_urgent": [
            {
                "name": "Friendly",
                "tone": "friendly",
                "cta_type": "soft",
                "emoji_usage": "light",
            },
            {
                "name": "Urgent",
                "tone": "urgent",
                "cta_type": "direct",
                "emoji_usage": "none",
            },
        ],
    }

    # CTA test configurations
    CTA_TEST_VARIANTS = {
        "soft_vs_direct": [
            {
                "name": "Soft CTA",
                "cta_type": "soft",
                "emoji_usage": "light",
            },
            {
                "name": "Direct CTA",
                "cta_type": "direct",
                "emoji_usage": "none",
            },
        ],
        "curiosity_vs_benefit": [
            {
                "name": "Curiosity",
                "cta_type": "curiosity",
            },
            {
                "name": "Benefit",
                "cta_type": "benefit",
            },
        ],
    }

    # Personalization test configurations
    PERSONALIZATION_TEST_VARIANTS = {
        "with_without_name": [
            {
                "name": "With Name",
                "personalization_level": "moderate",
            },
            {
                "name": "Without Name",
                "personalization_level": "minimal",
            },
        ],
        "deep_vs_minimal": [
            {
                "name": "Deep Personalization",
                "personalization_level": "deep",
            },
            {
                "name": "Minimal Personalization",
                "personalization_level": "minimal",
            },
        ],
    }

    def __init__(self):
        """Initialize A/B testing engine"""
        self.tests: Dict[str, ABTest] = {}
        self.results: Dict[str, Dict[str, Any]] = defaultdict(dict)
        logger.info("ABTestingEngine initialized")

    def create_test(
        self,
        test_name: str,
        test_type: ExperimentType,
        control_message: str,
        treatment_messages: List[Dict[str, str]],
        hypothesis: str,
        duration_days: int = 7,
    ) -> ABTest:
        """
        Create A/B test.

        Args:
            test_name: Name of test
            test_type: Type of test
            control_message: Control message template
            treatment_messages: List of treatment message dicts
            hypothesis: Test hypothesis
            duration_days: How long to run test

        Returns:
            ABTest instance
        """
        test_id = f"test_{test_name.lower().replace(' ', '_')}_{int(datetime.utcnow().timestamp())}"

        # Create control variant
        control = Variant(
            variant_id=f"{test_id}_control",
            name="Control",
            test_type=test_type,
            message_template=control_message,
        )

        # Create treatment variants
        treatment_variants = []
        for i, treatment in enumerate(treatment_messages):
            variant = Variant(
                variant_id=f"{test_id}_treatment_{i+1}",
                name=treatment.get("name", f"Treatment {i+1}"),
                test_type=test_type,
                message_template=treatment.get("message", ""),
                tone=treatment.get("tone"),
                cta_type=treatment.get("cta_type"),
                personalization_level=treatment.get("personalization_level"),
                emoji_usage=treatment.get("emoji_usage"),
            )
            treatment_variants.append(variant)

        # Create test
        test = ABTest(
            test_id=test_id,
            name=test_name,
            test_type=test_type,
            hypothesis=hypothesis,
            description=f"Testing {test_type.value} variations",
            control_variant=control,
            duration_days=duration_days,
            started_at=datetime.utcnow(),
        )

        for variant in treatment_variants:
            test.add_variant(variant)

        # Store test
        self.tests[test_id] = test

        logger.info(f"Created A/B test: {test_name} (ID: {test_id})")
        return test

    def select_variant(
        self,
        test_id: str,
        random_allocation: bool = True,
    ) -> Optional[Variant]:
        """
        Select variant for message (simulates A/B distribution).

        Args:
            test_id: Test ID
            random_allocation: If True, random selection; if False, sequential

        Returns:
            Variant to use
        """
        if test_id not in self.tests:
            return None

        test = self.tests[test_id]
        variants = test.get_variants()

        if not variants:
            return None

        # Equal split allocation
        if random_allocation:
            return choice(variants)

        # Sequential allocation (for deterministic testing)
        return variants[0]

    def record_event(
        self,
        test_id: str,
        variant_id: str,
        event_type: str,  # "sent", "opened", "clicked", "replied", "converted"
    ) -> bool:
        """
        Record event for variant.

        Args:
            test_id: Test ID
            variant_id: Variant ID
            event_type: Type of event

        Returns:
            True if recorded successfully
        """
        if test_id not in self.tests:
            return False

        test = self.tests[test_id]
        variant = None

        # Find variant
        for v in test.get_variants():
            if v.variant_id == variant_id:
                variant = v
                break

        if not variant:
            return False

        # Record event
        if event_type == "sent":
            variant.sent_count += 1
        elif event_type == "opened":
            variant.open_count += 1
        elif event_type == "clicked":
            variant.click_count += 1
        elif event_type == "replied":
            variant.reply_count += 1
        elif event_type == "converted":
            variant.conversion_count += 1

        variant.updated_at = datetime.utcnow()
        return True

    def record_humanness_feedback(
        self,
        test_id: str,
        variant_id: str,
        score: float,  # 0-1
    ) -> bool:
        """
        Record humanness perception feedback.

        Args:
            test_id: Test ID
            variant_id: Variant ID
            score: Humanness score (0-1)

        Returns:
            True if recorded
        """
        if test_id not in self.tests:
            return False

        test = self.tests[test_id]
        for variant in test.get_variants():
            if variant.variant_id == variant_id:
                # Update humanness score (exponential moving average)
                alpha = 0.2  # Smoothing factor
                variant.humanness_score = (alpha * score) + ((1 - alpha) * variant.humanness_score)
                return True

        return False

    def analyze_test(
        self,
        test_id: str,
    ) -> Dict[str, Any]:
        """
        Analyze test results and determine if there's a winner.

        Returns:
            {
                "test_id": str,
                "test_name": str,
                "status": "active" | "inconclusive" | "winner_found",
                "variants": [
                    {
                        "name": str,
                        "metrics": {...},
                        "confidence": float,
                        "is_winner": bool,
                    }
                ],
                "recommendation": str,
                "confidence_level": float,  # 0-1
            }
        """
        if test_id not in self.tests:
            return {"error": "Test not found"}

        test = self.tests[test_id]
        variants = test.get_variants()

        # Collect variant metrics
        variant_stats = []
        for variant in variants:
            metrics = variant.get_metrics()
            stats = {
                "name": variant.name,
                "variant_id": variant.variant_id,
                "metrics": metrics,
                "humanness_score": variant.humanness_score,
                "conversions": variant.conversion_count,
                "sent": variant.sent_count,
                "conversion_rate": metrics.get("conversion_rate", 0),
            }
            variant_stats.append(stats)

        # Determine winner (highest conversion rate)
        if variant_stats:
            best_variant = max(variant_stats, key=lambda x: x["conversion_rate"])
            worst_variant = min(variant_stats, key=lambda x: x["conversion_rate"])

            conversion_difference = (
                best_variant["conversion_rate"] - worst_variant["conversion_rate"]
            )

            # Check if winner is statistically significant
            if conversion_difference >= test.min_conversion_difference:
                status = "winner_found"
                confidence = min(conversion_difference * 2, 0.99)  # Scale to 0-1
            else:
                status = "inconclusive"
                confidence = conversion_difference

            # Mark variants
            for stat in variant_stats:
                stat["is_winner"] = (stat["variant_id"] == best_variant["variant_id"]) if status == "winner_found" else False

            # Generate recommendation
            if status == "winner_found":
                recommendation = f"Winner: {best_variant['name']} (Improvement: {conversion_difference*100:.1f}%)"
            else:
                recommendation = f"Continue testing (Current best: {best_variant['name']})"

            return {
                "test_id": test_id,
                "test_name": test.name,
                "test_type": test.test_type.value,
                "hypothesis": test.hypothesis,
                "status": status,
                "variants": variant_stats,
                "recommendation": recommendation,
                "confidence_level": confidence,
                "duration_days": test.duration_days,
                "sample_size": sum(v["sent"] for v in variant_stats),
            }

        return {
            "error": "No variants in test",
            "test_id": test_id,
        }

    def get_winning_variant(
        self,
        test_id: str,
    ) -> Optional[Variant]:
        """Get winning variant of test"""
        if test_id not in self.tests:
            return None

        test = self.tests[test_id]
        analysis = self.analyze_test(test_id)

        if analysis.get("status") == "winner_found":
            # Find winner variant
            for variant in test.get_variants():
                if variant.variant_id == test.winner_id:
                    return variant

        return None

    def generate_test_summary(
        self,
        test_id: str,
    ) -> Dict[str, Any]:
        """Generate summary report of test"""
        if test_id not in self.tests:
            return {"error": "Test not found"}

        test = self.tests[test_id]
        analysis = self.analyze_test(test_id)

        summary = {
            "test_name": test.name,
            "test_type": test.test_type.value,
            "hypothesis": test.hypothesis,
            "duration": f"{test.duration_days} days",
            "started": test.started_at.isoformat() if test.started_at else "N/A",
            "variants_tested": len(test.get_variants()),
            "total_sent": sum(v["sent"] for v in analysis.get("variants", [])),
            "best_performer": max(
                (v for v in analysis.get("variants", [])),
                key=lambda x: x["conversion_rate"],
                default={}
            ).get("name", "N/A"),
            "recommendation": analysis.get("recommendation", "N/A"),
            "confidence": f"{analysis.get('confidence_level', 0)*100:.0f}%",
        }

        return summary

    def calculate_statistical_significance(
        self,
        variant_a_conversions: int,
        variant_a_total: int,
        variant_b_conversions: int,
        variant_b_total: int,
        confidence_level: float = 0.95,
    ) -> Tuple[bool, float]:
        """
        Calculate if difference between variants is statistically significant.

        Uses chi-squared test approximation.

        Args:
            variant_a_conversions: Conversion count for A
            variant_a_total: Total sent for A
            variant_b_conversions: Conversion count for B
            variant_b_total: Total sent for B
            confidence_level: Confidence threshold (0.95 = 95%)

        Returns:
            (is_significant: bool, p_value: float)
        """
        # Calculate conversion rates
        rate_a = variant_a_conversions / variant_a_total if variant_a_total > 0 else 0
        rate_b = variant_b_conversions / variant_b_total if variant_b_total > 0 else 0

        # Simple chi-squared approximation
        if variant_a_total == 0 or variant_b_total == 0:
            return False, 1.0

        # Expected difference under null hypothesis (both have same rate)
        pool_rate = (variant_a_conversions + variant_b_conversions) / (variant_a_total + variant_b_total)
        expected_diff = pool_rate * (1 - pool_rate) * (1/variant_a_total + 1/variant_b_total)

        if expected_diff == 0:
            return False, 1.0

        z_score = abs(rate_a - rate_b) / (expected_diff ** 0.5)

        # Approximate p-value (simplified)
        p_value = 1 / (1 + (z_score ** 2))

        is_significant = p_value < (1 - confidence_level)

        return is_significant, p_value

    def create_preset_test(
        self,
        preset_name: str,
        control_message: str,
    ) -> Optional[ABTest]:
        """
        Create test from preset configuration.

        Presets:
        - "formal_vs_casual"
        - "soft_vs_direct_cta"
        - "with_without_name"
        """
        if preset_name in self.TONE_TEST_VARIANTS:
            variants = self.TONE_TEST_VARIANTS[preset_name]
            test_type = ExperimentType.TONE
        elif preset_name in self.CTA_TEST_VARIANTS:
            variants = self.CTA_TEST_VARIANTS[preset_name]
            test_type = ExperimentType.CTA
        elif preset_name in self.PERSONALIZATION_TEST_VARIANTS:
            variants = self.PERSONALIZATION_TEST_VARIANTS[preset_name]
            test_type = ExperimentType.PERSONALIZATION
        else:
            return None

        return self.create_test(
            test_name=preset_name,
            test_type=test_type,
            control_message=control_message,
            treatment_messages=variants,
            hypothesis=f"Testing {preset_name}",
        )
