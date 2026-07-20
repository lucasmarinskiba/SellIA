"""
Virtue Agent — Enforcement de honestidad, integridad, transparencia en ventas.

Principios:
1. Honesty: No fake claims, no misleading statements
2. Integrity: Match promise with delivery always
3. Respect: User-centric, never manipulative
4. Transparency: Disclose all limitations upfront
5. Value: Only recommend if truly valuable to user
"""

import logging
from typing import Dict, List, Any, Tuple
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class HonestySeverity(str, Enum):
    """Severity of honesty violation."""
    CRITICAL = "critical"  # Outright lie
    HIGH = "high"  # Misleading claim
    MEDIUM = "medium"  # Exaggerated benefit
    LOW = "low"  # Missing important caveat


class IntegrityCheck(str, Enum):
    """Types of integrity checks."""
    PROMISE_DELIVERY = "promise_delivery"  # Promise matches delivery
    TIMELINE_ADHERENCE = "timeline_adherence"  # Delivers on time
    QUALITY_CONSISTENCY = "quality_consistency"  # Quality matches claim
    CUSTOMER_SUCCESS = "customer_success"  # Customer actually wins


class VirtueAgent:
    """Enforces ethical sales practices."""

    # Prohibited phrases (outright lies)
    PROHIBITED_CLAIMS = [
        "guaranteed results",
        "100% success",
        "risk-free",
        "money-back guaranteed" if not verified else "",
        "fastest in market" if not verified else "",
        "only solution",
        "works for everyone",
    ]

    # High-risk exaggerations to flag
    EXAGGERATION_PATTERNS = [
        ("will", "could", "might"),  # Replace certainty with possibility
        ("always", "often", "sometimes"),  # Temper absolute claims
        ("everyone", "many people", "some people"),  # Reduce universality
    ]

    # Required transparency statements
    REQUIRED_TRANSPARENCY = {
        "trial": "Must disclose trial period end date",
        "pricing": "Must show full pricing breakdown",
        "limitations": "Must disclose product limitations",
        "upsells": "Must disclose upsell opportunities",
        "data_usage": "Must disclose data usage clearly",
        "refund_policy": "Must be explicit about refund terms",
    }

    @staticmethod
    def validate_honesty(claim: str, product_data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate if a claim is honest and not misleading.

        Returns:
            (is_honest, details)
                - is_honest: True if claim passes all checks
                - details: {severity, reason, suggestion, fix}
        """

        details = {
            "is_honest": True,
            "violations": [],
            "warnings": [],
            "suggestions": [],
        }

        # Check 1: Prohibited claims
        for prohibited in VirtueAgent.PROHIBITED_CLAIMS:
            if prohibited.lower() in claim.lower():
                details["violations"].append({
                    "type": "prohibited_claim",
                    "severity": HonestySeverity.CRITICAL,
                    "claim": prohibited,
                    "reason": f"'{prohibited}' is a prohibited absolute claim",
                    "suggestion": f"Reframe as 'often helps', 'works for many', 'typically', etc.",
                })
                details["is_honest"] = False

        # Check 2: Unverified superlatives
        superlatives = ["best", "fastest", "cheapest", "#1", "only"]
        for word in superlatives:
            if word.lower() in claim.lower():
                if not product_data.get(f"verified_{word}", False):
                    details["warnings"].append({
                        "type": "unverified_superlative",
                        "severity": HonestySeverity.HIGH,
                        "claim": word,
                        "reason": f"'{word}' not verified in product data",
                        "suggestion": f"Use 'among the', 'typically', or remove superlative",
                    })

        # Check 3: Certainty language (should use possibility)
        certainty_words = ["will", "always", "never", "guaranteed", "certain"]
        for word in certainty_words:
            if word.lower() in claim.lower():
                if not product_data.get("highly_predictable", False):
                    details["warnings"].append({
                        "type": "overconfident_language",
                        "severity": HonestySeverity.MEDIUM,
                        "word": word,
                        "reason": "Using absolute certainty without verification",
                        "suggestion": "Replace with 'typically', 'often', 'can', 'might'",
                    })

        # Check 4: Missing required transparency
        for required_type, requirement in VirtueAgent.REQUIRED_TRANSPARENCY.items():
            if required_type in product_data:
                if not claim.lower().__contains__(required_type) and product_data.get(f"must_disclose_{required_type}", True):
                    details["suggestions"].append({
                        "type": "missing_transparency",
                        "requirement": required_type,
                        "message": requirement,
                    })

        return details["is_honest"], details

    @staticmethod
    def check_integrity(
        promise: str,
        delivery: Dict[str, Any],
        timeline: Dict[str, Any],
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if promise matches actual delivery.

        Returns:
            (integrity_maintained, details)
        """

        details = {
            "integrity_maintained": True,
            "checks": {},
            "gaps": [],
            "actions": [],
        }

        # Check 1: Promise vs Delivery
        if delivery:
            delivery_quality = delivery.get("quality_score", 0)
            if delivery_quality < 0.7:
                details["checks"]["delivery"] = {
                    "status": "warning",
                    "score": delivery_quality,
                    "gap": f"Delivery quality {delivery_quality:.0%} below promise",
                }
                details["integrity_maintained"] = False
                details["gaps"].append("Delivery quality gap")

        # Check 2: Timeline adherence
        if timeline:
            promised_date = timeline.get("promised_delivery")
            actual_date = timeline.get("actual_delivery")

            if promised_date and actual_date:
                from datetime import datetime
                try:
                    delta_days = (datetime.fromisoformat(actual_date) -
                                datetime.fromisoformat(promised_date)).days
                    if delta_days > 0:
                        details["checks"]["timeline"] = {
                            "status": "delayed",
                            "days_late": delta_days,
                        }
                        details["gaps"].append(f"Delivery {delta_days} days late")
                        details["integrity_maintained"] = False
                except:
                    pass

        # Check 3: Feature parity
        promised_features = set(delivery.get("promised_features", []))
        delivered_features = set(delivery.get("delivered_features", []))

        missing_features = promised_features - delivered_features
        if missing_features:
            details["checks"]["features"] = {
                "status": "incomplete",
                "missing": list(missing_features),
            }
            details["gaps"].append(f"Missing {len(missing_features)} promised features")
            details["integrity_maintained"] = False

            # Action: explain gaps and offer remedy
            details["actions"].append({
                "type": "communicate_gap",
                "message": f"Transparently explain why features {missing_features} are missing",
                "remedy": "Offer timeline + compensation or alternatives",
            })

        # Check 4: Quality consistency
        expected_quality = delivery.get("expected_quality", 0)
        actual_quality = delivery.get("actual_quality", 0)

        if expected_quality > 0 and actual_quality / expected_quality < 0.85:
            details["checks"]["quality"] = {
                "status": "degraded",
                "expectation": expected_quality,
                "actual": actual_quality,
            }
            details["integrity_maintained"] = False

        return details["integrity_maintained"], details

    @staticmethod
    def enforce_respect_framework(
        audience: Dict[str, Any],
        message: str,
        intent: str,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if message is respectful and not manipulative.

        Checks:
        1. No dark patterns (false urgency, fake scarcity)
        2. No targeting vulnerabilities (not preying on pain)
        3. User-centric (focused on user benefit, not sales)
        4. Consent (no spam, no harassment)
        5. Autonomy (respects user choice)
        """

        details = {
            "respectful": True,
            "violations": [],
            "warnings": [],
        }

        # Dark pattern detection
        dark_patterns = {
            "false_urgency": ["hurry", "last chance", "today only", "act now", "before it's gone"],
            "fake_scarcity": ["only 3 left", "running out", "limited spots", "exclusive"],
            "social_proof_abuse": ["everyone is buying", "trending", "viral", "everyone loves"],
            "authority_abuse": ["doctors recommend", "experts say", "scientific", "proven"],
        }

        for pattern, keywords in dark_patterns.items():
            for keyword in keywords:
                if keyword.lower() in message.lower():
                    # Check if claim is verified
                    if not audience.get(f"verified_{pattern}", False):
                        details["violations"].append({
                            "type": "dark_pattern",
                            "pattern": pattern,
                            "keyword": keyword,
                            "severity": HonestySeverity.HIGH,
                            "message": f"Unverified '{pattern}' detected",
                        })
                        details["respectful"] = False

        # Manipulation check: targeting vulnerabilities
        emotional_triggers = ["desperate", "fail", "stupid", "worthless", "shame", "afraid"]
        for trigger in emotional_triggers:
            if trigger.lower() in message.lower():
                details["warnings"].append({
                    "type": "emotional_manipulation",
                    "trigger": trigger,
                    "message": "Message may be manipulating emotional vulnerabilities",
                    "fix": "Remove emotional triggers, focus on rational benefits",
                })

        # User-centric check
        user_benefit_keywords = ["you save", "you gain", "you get", "your success", "your benefit"]
        seller_benefit_keywords = ["our growth", "our profit", "our revenue"]

        user_benefit_count = sum(1 for kw in user_benefit_keywords if kw in message.lower())
        seller_benefit_count = sum(1 for kw in seller_benefit_keywords if kw in message.lower())

        if seller_benefit_count > user_benefit_count:
            details["warnings"].append({
                "type": "not_user_centric",
                "message": "Message is more focused on seller benefits than user benefits",
                "fix": "Reframe message to emphasize user value proposition",
            })

        return details["respectful"], details

    @staticmethod
    def check_transparency(
        message: str,
        product: Dict[str, Any],
        must_disclose: List[str],
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if message includes required transparency.

        Returns:
            (fully_transparent, details)
        """

        details = {
            "transparent": True,
            "disclosed": [],
            "missing": [],
            "suggestions": [],
        }

        for item in must_disclose:
            item_lower = item.lower()
            if item_lower in message.lower():
                details["disclosed"].append(item)
            else:
                details["missing"].append(item)
                details["transparent"] = False

                if item == "limitations":
                    details["suggestions"].append({
                        "type": "missing_limitation",
                        "message": "Add product limitations: 'Note: works best with X, may not suit Y'",
                    })
                elif item == "pricing":
                    details["suggestions"].append({
                        "type": "missing_pricing",
                        "message": "Full pricing must be visible: base + taxes + fees",
                    })
                elif item == "trial_length":
                    details["suggestions"].append({
                        "type": "missing_trial",
                        "message": f"Trial ends on [DATE]. Disclose cancellation terms.",
                    })
                elif item == "refund_policy":
                    details["suggestions"].append({
                        "type": "missing_refund",
                        "message": "Be explicit: 'X days money-back guarantee, no questions'",
                    })

        return details["transparent"], details

    @staticmethod
    def score_virtue(
        claim: str,
        product: Dict[str, Any],
        delivery: Dict[str, Any],
        audience: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Overall virtue score (0-100).

        Factors:
        - Honesty (40%)
        - Integrity (30%)
        - Respect (20%)
        - Transparency (10%)
        """

        honesty_score = 0
        integrity_score = 0
        respect_score = 0
        transparency_score = 0

        # Honesty
        is_honest, honesty_details = VirtueAgent.validate_honesty(claim, product)
        honesty_score = 100 if is_honest else max(0, 100 - len(honesty_details["violations"]) * 25)

        # Integrity
        is_integral, integrity_details = VirtueAgent.check_integrity(
            claim,
            delivery,
            product.get("timeline", {}),
        )
        integrity_score = 100 if is_integral else max(0, 100 - len(integrity_details["gaps"]) * 20)

        # Respect
        is_respectful, respect_details = VirtueAgent.enforce_respect_framework(
            audience,
            claim,
            "sales",
        )
        respect_score = 100 if is_respectful else max(0, 100 - len(respect_details["violations"]) * 15)

        # Transparency (simplified)
        transparency_score = 90 if len(honesty_details.get("suggestions", [])) < 3 else 60

        # Weighted score
        virtue_score = (
            honesty_score * 0.40 +
            integrity_score * 0.30 +
            respect_score * 0.20 +
            transparency_score * 0.10
        )

        return {
            "virtue_score": int(virtue_score),
            "passed": virtue_score >= 80,
            "components": {
                "honesty": honesty_score,
                "integrity": integrity_score,
                "respect": respect_score,
                "transparency": transparency_score,
            },
            "violations": honesty_details.get("violations", []),
            "warnings": (
                honesty_details.get("warnings", []) +
                respect_details.get("warnings", [])
            ),
            "recommendations": honesty_details.get("suggestions", []),
        }
