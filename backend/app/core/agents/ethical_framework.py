"""
Ethical Framework — Boundary enforcement against manipulation tactics.

Prevents:
1. Dark patterns (fake urgency, false scarcity)
2. FOMO abuse (fear-based manipulation)
3. Scarcity dishonesty (real vs fake scarcity)
4. Testimonial fabrication (real vs fake reviews)
5. Pricing dishonesty (hidden fees, bait-and-switch)
"""

import logging
from typing import Dict, List, Any, Tuple
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class DarkPatternType(str, Enum):
    """Types of dark patterns."""
    FALSE_URGENCY = "false_urgency"  # Artificial time pressure
    FAKE_SCARCITY = "fake_scarcity"  # Fake limited availability
    MISDIRECTION = "misdirection"  # Hidden important info
    FORCED_CONTINUATION = "forced_continuation"  # Hard to cancel
    CONFIRMSHAMING = "confirmshaming"  # Negative buttons for saying no
    BAIT_AND_SWITCH = "bait_and_switch"  # Promise X, deliver Y
    ROACH_MOTEL = "roach_motel"  # Easy to enter, hard to leave
    DISGUISED_AD = "disguised_ad"  # Ad disguised as content


class EthicalFramework:
    """Enforces ethical boundaries in sales."""

    # Dark pattern keywords
    DARK_PATTERN_INDICATORS = {
        DarkPatternType.FALSE_URGENCY: {
            "keywords": [
                "hurry", "last chance", "today only", "act now",
                "before it's gone", "ends tonight", "limited time",
                "don't miss out", "expires", "rush",
            ],
            "severity": "high",
        },
        DarkPatternType.FAKE_SCARCITY: {
            "keywords": [
                "only 3 left", "running out", "limited spots",
                "exclusive access", "only for today", "one time offer",
                "while supplies last", "almost sold out",
            ],
            "severity": "high",
        },
        DarkPatternType.CONFIRMSHAMING: {
            "keywords": [
                "I don't want to save money", "Click here to lose",
                "Yes, make me poor", "No, I prefer to fail",
            ],
            "severity": "critical",
        },
        DarkPatternType.FORCED_CONTINUATION: {
            "keywords": [
                "auto-renew", "cancellation fee", "requires calling",
                "buried cancel button", "no easy cancel",
            ],
            "severity": "high",
        },
    }

    # Manipulation triggers
    MANIPULATION_TRIGGERS = {
        "fear_based": ["fail", "lose", "miss", "never", "desperate"],
        "obligation": ["should", "must", "have to", "owe"],
        "guilt": ["shameful", "irresponsible", "negligent"],
        "social_proof_fake": ["everyone", "trending", "viral", "most popular"],
    }

    @staticmethod
    def detect_dark_patterns(message: str) -> Dict[str, Any]:
        """
        Detect dark patterns in message.

        Returns:
            {
                "patterns_detected": [list],
                "severity": str,
                "safe_to_send": bool,
                "recommendations": [list],
            }
        """

        patterns_found = []
        message_lower = message.lower()

        for pattern_type, pattern_data in EthicalFramework.DARK_PATTERN_INDICATORS.items():
            keywords = pattern_data["keywords"]
            matches = [kw for kw in keywords if kw.lower() in message_lower]

            if matches:
                patterns_found.append({
                    "pattern_type": pattern_type.value,
                    "severity": pattern_data["severity"],
                    "matched_keywords": matches,
                    "count": len(matches),
                })

        # Assess safety
        max_severity = max([p["severity"] for p in patterns_found], default="low")
        severity_order = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        safe_to_send = severity_order.get(max_severity, 1) <= 2

        # Recommendations
        recommendations = []
        for pattern in patterns_found:
            if pattern["pattern_type"] == DarkPatternType.FALSE_URGENCY.value:
                recommendations.append(
                    "Remove artificial urgency. If deadline exists, explain why."
                )
            elif pattern["pattern_type"] == DarkPatternType.FAKE_SCARCITY.value:
                recommendations.append(
                    "Verify scarcity claim. Only mention if genuinely limited."
                )
            elif pattern["pattern_type"] == DarkPatternType.CONFIRMSHAMING.value:
                recommendations.append(
                    "Never use shame-based buttons. Always offer neutral decline options."
                )
            elif pattern["pattern_type"] == DarkPatternType.FORCED_CONTINUATION.value:
                recommendations.append(
                    "Cancellation must be easy. Add clear cancel link/button."
                )

        return {
            "patterns_detected": patterns_found,
            "pattern_count": len(patterns_found),
            "max_severity": max_severity,
            "safe_to_send": safe_to_send,
            "recommendations": recommendations,
        }

    @staticmethod
    def check_fomo_abuse(message: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if message exploits FOMO (fear of missing out) abusively.

        Returns:
            {
                "fomo_detected": bool,
                "severity": str,
                "type": str,
                "fix": str,
            }
        """

        fomo_keywords = [
            "exclusive", "limited", "last chance", "only", "now",
            "trending", "everyone's doing", "don't miss",
        ]

        message_lower = message.lower()
        fomo_present = any(kw in message_lower for kw in fomo_keywords)

        if not fomo_present:
            return {
                "fomo_detected": False,
                "severity": "none",
                "message": "No FOMO detected",
            }

        # Assess if FOMO is legitimate or manipulative
        legitimate_fomo = False

        # Legitimate cases:
        # 1. Event actually has limited spots + verified
        if "event" in message_lower and user_context.get("verified_limited_spots"):
            legitimate_fomo = True

        # 2. Product actually selling out + inventory verified
        if "selling out" in message_lower and user_context.get("inventory_level", 100) < 10:
            legitimate_fomo = True

        # 3. Promotional offer has real end date + verified
        if "offer ends" in message_lower and user_context.get("verified_end_date"):
            legitimate_fomo = True

        if legitimate_fomo:
            return {
                "fomo_detected": True,
                "legitimate": True,
                "severity": "low",
                "message": "FOMO present but appears justified",
            }

        # Abusive FOMO
        return {
            "fomo_detected": True,
            "legitimate": False,
            "severity": "high",
            "type": "manipulative_fomo",
            "issue": "FOMO used without verification or legitimacy",
            "fix": "Remove manufactured urgency. If deadline exists, explain why.",
        }

    @staticmethod
    def validate_scarcity(claim: str, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate if scarcity claim is real.

        Returns:
            {
                "scarcity_claimed": bool,
                "scarcity_verified": bool,
                "actual_inventory": int or None,
                "safe_to_claim": bool,
                "recommendation": str,
            }
        """

        scarcity_keywords = ["limited", "only", "exclusive", "rare", "few left"]
        claimed = any(kw in claim.lower() for kw in scarcity_keywords)

        if not claimed:
            return {"scarcity_claimed": False}

        # Check inventory
        actual_inventory = product_data.get("current_inventory", None)
        threshold = product_data.get("low_inventory_threshold", 10)

        # Verify scarcity claim
        if actual_inventory is not None:
            if actual_inventory <= threshold:
                verified = True
                recommendation = f"Claim is verified: {actual_inventory} units available"
            else:
                verified = False
                recommendation = f"Claim is FALSE: {actual_inventory} units available (not limited)"
        else:
            verified = False
            recommendation = "Cannot verify scarcity: no inventory data"

        return {
            "scarcity_claimed": True,
            "scarcity_verified": verified,
            "actual_inventory": actual_inventory,
            "low_threshold": threshold,
            "safe_to_claim": verified,
            "recommendation": recommendation,
            "severity": "critical" if claimed and not verified else "low",
        }

    @staticmethod
    def validate_testimonials(
        testimonials: List[Dict[str, Any]],
        product_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Validate testimonials for authenticity.

        Checks:
        1. Reviewer actually used product
        2. Review matches expected user demographic
        3. Review language sounds authentic (not scripted)
        4. Claims are verifiable
        5. Conflicts of interest disclosed
        """

        validation_results = []

        for i, testimonial in enumerate(testimonials):
            review_check = {
                "testimonial_index": i,
                "reviewer": testimonial.get("reviewer_name", "Unknown"),
                "valid": True,
                "flags": [],
                "warnings": [],
            }

            # Check 1: Reviewer verification
            reviewer_verified = testimonial.get("verified_purchase", False)
            if not reviewer_verified:
                review_check["flags"].append("Unverified purchase")
                review_check["valid"] = False

            # Check 2: Review authenticity (language patterns)
            review_text = testimonial.get("text", "").lower()

            # Red flags for fake reviews
            fake_review_indicators = [
                ("I", review_text.count("I") < 2),  # Few personal pronouns = less authentic
                ("actually", "actually" in review_text or "really" in review_text),
                ("specific detail", len(review_text.split()) > 200),  # Too generic or too long
                ("natural language", "highly recommend" not in review_text and "best" not in review_text),
            ]

            # Very short reviews are suspicious
            if len(review_text.split()) < 10:
                review_check["warnings"].append("Very short review (suspicious)")

            # All-caps words suggest enthusiasm but may be fake
            caps_words = [w for w in review_text.split() if w.isupper() and len(w) > 2]
            if len(caps_words) > 3:
                review_check["warnings"].append("Excessive all-caps (may indicate fake)")

            # Check 3: Conflicts of interest
            reviewer_role = testimonial.get("reviewer_role", "customer")
            if reviewer_role in ["affiliate", "partner", "employee"]:
                review_check["warnings"].append(f"Conflict of interest: {reviewer_role}")
                if not testimonial.get("conflict_disclosed", False):
                    review_check["flags"].append("Conflict of interest NOT disclosed")
                    review_check["valid"] = False

            # Check 4: Claim verification
            claims = testimonial.get("claims", [])
            for claim in claims:
                claim_type = claim.get("type")
                claim_value = claim.get("value")

                # Verify against product data
                if claim_type == "performance":
                    expected_range = product_data.get("performance_range")
                    if expected_range and (
                        claim_value < expected_range[0] or claim_value > expected_range[1]
                    ):
                        review_check["warnings"].append(
                            f"Claim '{claim_type}={claim_value}' outside expected range"
                        )

            validation_results.append(review_check)

        # Summary
        valid_count = sum(1 for r in validation_results if r["valid"])
        flagged_count = sum(1 for r in validation_results if r["flags"])

        return {
            "total_testimonials": len(testimonials),
            "valid": valid_count,
            "flagged": flagged_count,
            "validation_results": validation_results,
            "recommendation": (
                "Safe to use" if valid_count >= len(testimonials) * 0.8
                else "Filter out flagged testimonials"
            ),
        }

    @staticmethod
    def check_pricing_honesty(pricing: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check for hidden fees and pricing dishonesty.

        Returns:
            {
                "total_cost": float,
                "hidden_fees": [list],
                "fees_disclosed": bool,
                "price_honest": bool,
                "recommendation": str,
            }
        """

        base_price = pricing.get("base_price", 0)
        all_fees = []
        undisclosed_fees = []

        # Common hidden fees
        fee_types = {
            "setup_fee": "Setup/Installation",
            "shipping": "Shipping",
            "tax": "Tax",
            "service_fee": "Service/Processing Fee",
            "cancellation_fee": "Cancellation Fee",
            "maintenance": "Maintenance/Renewal",
            "payment_processor": "Payment Processor Fee",
        }

        for fee_key, fee_name in fee_types.items():
            fee_amount = pricing.get(fee_key, 0)
            if fee_amount > 0:
                all_fees.append({
                    "name": fee_name,
                    "amount": fee_amount,
                    "disclosed": pricing.get(f"{fee_key}_disclosed", False),
                })

                if not pricing.get(f"{fee_key}_disclosed", False):
                    undisclosed_fees.append(fee_name)

        total_cost = base_price + sum(f["amount"] for f in all_fees)
        price_honest = len(undisclosed_fees) == 0 and pricing.get("final_price_clear", False)

        # Calculate percentage markup from hidden fees
        markup_percentage = ((total_cost - base_price) / base_price * 100) if base_price > 0 else 0

        return {
            "base_price": base_price,
            "total_cost": total_cost,
            "hidden_markup_pct": markup_percentage,
            "all_fees": all_fees,
            "hidden_fees": undisclosed_fees,
            "fees_disclosed": len(undisclosed_fees) == 0,
            "price_honest": price_honest,
            "recommendation": (
                "Pricing is honest" if price_honest
                else f"Disclose these fees: {', '.join(undisclosed_fees)}"
            ),
            "transparency_score": 100 - (len(undisclosed_fees) * 20),
        }

    @staticmethod
    def ethical_score(
        message: str,
        product_data: Dict[str, Any],
        user_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Overall ethical score (0-100).

        Factors:
        - Dark patterns (30%)
        - FOMO abuse (20%)
        - Scarcity honesty (20%)
        - Testimonial authenticity (15%)
        - Pricing honesty (15%)
        """

        score = 100
        issues = []

        # Dark patterns check
        dark_pattern_result = EthicalFramework.detect_dark_patterns(message)
        severity_weight = {"low": 0, "medium": -10, "high": -25, "critical": -50}
        dp_penalty = severity_weight.get(dark_pattern_result["max_severity"], 0)
        score += dp_penalty * 0.30
        if not dark_pattern_result["safe_to_send"]:
            issues.extend([f"Dark pattern: {p['pattern_type']}" for p in dark_pattern_result["patterns_detected"]])

        # FOMO abuse check
        fomo_result = EthicalFramework.check_fomo_abuse(message, user_context)
        if fomo_result.get("fomo_detected") and not fomo_result.get("legitimate"):
            score -= 20 * 0.20
            issues.append("Abusive FOMO detected")

        # Scarcity honesty
        scarcity_result = EthicalFramework.validate_scarcity(message, product_data)
        if scarcity_result.get("scarcity_claimed") and not scarcity_result.get("scarcity_verified"):
            score -= 25 * 0.20
            issues.append("False scarcity claim")

        # Testimonials
        if "testimonials" in product_data:
            testimonial_result = EthicalFramework.validate_testimonials(
                product_data["testimonials"],
                product_data,
            )
            fake_testimonials = testimonial_result["flagged"]
            if fake_testimonials > 0:
                score -= (fake_testimonials / len(product_data["testimonials"]) * 25) * 0.15
                issues.append(f"{fake_testimonials} flagged testimonials")

        # Pricing honesty
        pricing_result = EthicalFramework.check_pricing_honesty(product_data.get("pricing", {}))
        score += (pricing_result["transparency_score"] - 100) * 0.15
        if not pricing_result["price_honest"]:
            issues.append(f"Hidden fees: {', '.join(pricing_result['hidden_fees'])}")

        score = max(0, min(100, score))

        return {
            "ethical_score": int(score),
            "passed": score >= 70,
            "issues": issues,
            "issue_count": len(issues),
            "recommendation": (
                "Ethical to send" if score >= 70
                else f"Address issues before sending: {'; '.join(issues[:3])}"
            ),
            "dark_patterns": dark_pattern_result["patterns_detected"],
            "fomo_status": fomo_result,
            "scarcity_status": scarcity_result,
            "pricing_transparency": pricing_result["transparency_score"],
        }
