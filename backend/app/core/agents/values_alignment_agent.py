"""
Values Alignment Agent — Ensures all recommendations align with user's values.

Workflow:
1. Extract user values from profile, behavior, feedback
2. Score each recommendation against user values
3. Detect conflicts (sales vs user values)
4. Recommend ethical path forward
5. Learn and improve alignment over time
"""

import logging
from typing import Dict, List, Any, Tuple
from enum import Enum
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ValueType(str, Enum):
    """User value categories."""
    FINANCIAL = "financial"  # Save money, ROI
    TIME = "time"  # Save time, efficiency
    HEALTH = "health"  # Wellness, safety
    ENVIRONMENTAL = "environmental"  # Sustainability
    SOCIAL = "social"  # Family, community, relationships
    ETHICAL = "ethical"  # Fair trade, no exploitation
    PRIVACY = "privacy"  # Data protection
    GROWTH = "growth"  # Learning, development
    QUALITY = "quality"  # Excellence, craftsmanship
    INDEPENDENCE = "independence"  # Autonomy, freedom


class AlignmentSeverity(str, Enum):
    """Severity of value conflict."""
    ALIGNED = "aligned"  # Perfectly aligned
    NEUTRAL = "neutral"  # No conflict
    MINOR_CONFLICT = "minor_conflict"  # Small trade-off
    MODERATE_CONFLICT = "moderate_conflict"  # Meaningful trade-off
    CRITICAL_CONFLICT = "critical_conflict"  # Contradicts core value


class ValuesAlignmentAgent:
    """Ensures recommendations respect user values."""

    # Value extraction patterns (from behavior)
    VALUE_INDICATORS = {
        ValueType.FINANCIAL: [
            "budget", "save money", "cheap", "discount", "ROI", "investment",
            "affordability", "cost-effective", "free", "price",
        ],
        ValueType.TIME: [
            "busy", "save time", "quick", "fast", "efficient", "productivity",
            "automate", "streamline", "urgent", "deadline",
        ],
        ValueType.HEALTH: [
            "wellness", "health", "safety", "exercise", "nutrition", "mental",
            "wellbeing", "stress", "sleep", "recovery",
        ],
        ValueType.ENVIRONMENTAL: [
            "sustainable", "eco", "green", "carbon", "plastic", "recycling",
            "renewable", "organic", "environment", "climate",
        ],
        ValueType.SOCIAL: [
            "family", "community", "relationship", "friend", "social", "connection",
            "team", "collaboration", "support", "together",
        ],
        ValueType.ETHICAL: [
            "ethical", "fair", "honest", "transparency", "no exploitation",
            "responsible", "values", "principles", "integrity",
        ],
        ValueType.PRIVACY: [
            "privacy", "data", "tracking", "surveillance", "personal", "confidential",
            "encryption", "secure", "anonymous", "control",
        ],
        ValueType.GROWTH: [
            "learn", "develop", "improve", "skill", "education", "course",
            "knowledge", "progress", "mastery", "challenge",
        ],
        ValueType.QUALITY: [
            "quality", "premium", "excellence", "craftsmanship", "best", "premium",
            "durable", "reliable", "top-tier", "superior",
        ],
        ValueType.INDEPENDENCE: [
            "freedom", "autonomy", "independent", "control", "choose", "flexible",
            "options", "customizable", "own", "self-reliant",
        ],
    }

    @staticmethod
    def extract_user_values(
        user_profile: Dict[str, Any],
        user_behavior: List[Dict[str, Any]],
        user_feedback: List[str],
    ) -> Dict[str, Any]:
        """
        Extract user values from profile, behavior, and feedback.

        Returns:
            {
                "values": {value_type: score},
                "primary_values": [list],
                "secondary_values": [list],
                "confidence": {value_type: confidence_score},
                "extracted_from": [list of sources],
            }
        """

        value_scores = {v.value: 0 for v in ValueType}
        value_confidence = {v.value: 0 for v in ValueType}
        extraction_sources = []

        # 1. Extract from profile
        if user_profile:
            for value_type, keywords in ValuesAlignmentAgent.VALUE_INDICATORS.items():
                profile_text = f"{user_profile.get('description', '')} {user_profile.get('bio', '')}"
                keyword_matches = sum(
                    1 for kw in keywords if kw.lower() in profile_text.lower()
                )
                if keyword_matches > 0:
                    value_scores[value_type.value] += keyword_matches * 10
                    value_confidence[value_type.value] = min(100, keyword_matches * 15)
                    extraction_sources.append(f"profile")

        # 2. Extract from behavior
        if user_behavior:
            for behavior_item in user_behavior:
                action = behavior_item.get("action", "")
                for value_type, keywords in ValuesAlignmentAgent.VALUE_INDICATORS.items():
                    if any(kw.lower() in action.lower() for kw in keywords):
                        value_scores[value_type.value] += 25
                        value_confidence[value_type.value] = min(100,
                                                                 value_confidence[value_type.value] + 25)
                        if "behavior" not in extraction_sources:
                            extraction_sources.append("behavior")

        # 3. Extract from feedback
        if user_feedback:
            feedback_text = " ".join(user_feedback).lower()
            for value_type, keywords in ValuesAlignmentAgent.VALUE_INDICATORS.items():
                keyword_matches = sum(1 for kw in keywords if kw.lower() in feedback_text)
                if keyword_matches > 0:
                    value_scores[value_type.value] += keyword_matches * 15
                    value_confidence[value_type.value] = min(100,
                                                            value_confidence[value_type.value] + 20)
                    if "feedback" not in extraction_sources:
                        extraction_sources.append("feedback")

        # Normalize scores
        for value_type in value_scores:
            value_scores[value_type] = min(100, value_scores[value_type])

        # Rank values
        sorted_values = sorted(value_scores.items(), key=lambda x: x[1], reverse=True)
        primary_values = [v[0] for v in sorted_values[:3] if v[1] > 30]
        secondary_values = [v[0] for v in sorted_values[3:6] if v[1] > 20]

        return {
            "values": value_scores,
            "primary_values": primary_values,
            "secondary_values": secondary_values,
            "confidence": value_confidence,
            "extracted_from": extraction_sources,
            "extraction_timestamp": datetime.utcnow().isoformat(),
        }

    @staticmethod
    def score_recommendation_alignment(
        recommendation: Dict[str, Any],
        user_values: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Score how well a recommendation aligns with user values.

        Returns:
            {
                "alignment_score": 0-100,
                "aligned_values": [list],
                "conflicting_values": [list],
                "neutral_values": [list],
                "severity": AlignmentSeverity,
                "reasoning": str,
            }
        """

        alignment_score = 50
        aligned_values = []
        conflicting_values = []
        neutral_values = []

        user_primary = set(user_values.get("primary_values", []))
        user_secondary = set(user_values.get("secondary_values", []))
        rec_text = f"{recommendation.get('description', '')} {recommendation.get('features', '')}"
        rec_text_lower = rec_text.lower()

        for value_type in ValueType:
            keywords = ValuesAlignmentAgent.VALUE_INDICATORS[value_type]
            keyword_matches = sum(1 for kw in keywords if kw.lower() in rec_text_lower)

            if keyword_matches > 0:
                if value_type.value in user_primary:
                    alignment_score += keyword_matches * 8
                    aligned_values.append(value_type.value)
                elif value_type.value in user_secondary:
                    alignment_score += keyword_matches * 4
                    aligned_values.append(value_type.value)
                else:
                    neutral_values.append(value_type.value)

        # Check for value conflicts
        conflict_indicators = {
            ValueType.PRIVACY: ["track", "data collection", "analytics", "third party"],
            ValueType.ENVIRONMENTAL: ["plastic", "shipping", "carbon", "waste"],
            ValueType.ETHICAL: ["exploited", "cheap labor", "non-fair trade"],
            ValueType.HEALTH: ["addictive", "harmful", "risky", "unsafe"],
            ValueType.FINANCIAL: ["expensive", "premium pricing", "upsell"],
        }

        for value_type, conflict_keywords in conflict_indicators.items():
            if value_type.value in user_primary or value_type.value in user_secondary:
                for conflict_kw in conflict_keywords:
                    if conflict_kw.lower() in rec_text_lower:
                        alignment_score -= 20
                        conflicting_values.append(value_type.value)
                        break

        alignment_score = max(0, min(100, alignment_score))

        # Determine severity
        if alignment_score >= 80:
            severity = AlignmentSeverity.ALIGNED
        elif alignment_score >= 60:
            severity = AlignmentSeverity.NEUTRAL
        elif alignment_score >= 40:
            if conflicting_values:
                severity = AlignmentSeverity.MINOR_CONFLICT
            else:
                severity = AlignmentSeverity.NEUTRAL
        elif alignment_score >= 20:
            severity = AlignmentSeverity.MODERATE_CONFLICT
        else:
            severity = AlignmentSeverity.CRITICAL_CONFLICT

        # Build reasoning
        reasoning_parts = []
        if aligned_values:
            reasoning_parts.append(f"Aligns with user values: {', '.join(aligned_values)}")
        if conflicting_values:
            reasoning_parts.append(f"Conflicts with: {', '.join(conflicting_values)}")
        if not aligned_values and not conflicting_values:
            reasoning_parts.append("Neutral to user values")

        return {
            "alignment_score": int(alignment_score),
            "severity": severity.value,
            "aligned_values": aligned_values,
            "conflicting_values": conflicting_values,
            "neutral_values": neutral_values,
            "reasoning": ". ".join(reasoning_parts),
            "passed": alignment_score >= 60,
        }

    @staticmethod
    def detect_conflicts(
        recommendation: Dict[str, Any],
        user_values: Dict[str, Any],
        sales_goal: str,
    ) -> Dict[str, Any]:
        """
        Detect conflicts between sales goal and user values.

        Returns:
            {
                "conflicts_detected": bool,
                "conflicts": [
                    {
                        "type": "sales_vs_user_value",
                        "description": str,
                        "severity": str,
                        "user_value": str,
                        "sales_pressure": str,
                        "recommendation": str,
                    }
                ],
            }
        """

        conflicts = []

        # Common conflict patterns
        conflict_patterns = {
            "high_price_vs_financial": {
                "keywords": ["premium", "expensive", "high price"],
                "user_value": ValueType.FINANCIAL,
                "suggestion": "Offer payment plan or lower-tier option",
            },
            "data_collection_vs_privacy": {
                "keywords": ["track", "data", "analytics"],
                "user_value": ValueType.PRIVACY,
                "suggestion": "Clarify data handling, offer opt-outs",
            },
            "time_commitment_vs_independence": {
                "keywords": ["lock-in", "contract", "commitment"],
                "user_value": ValueType.INDEPENDENCE,
                "suggestion": "Offer flexibility, no lock-in terms",
            },
            "resource_intensive_vs_environmental": {
                "keywords": ["plastic", "shipping", "energy"],
                "user_value": ValueType.ENVIRONMENTAL,
                "suggestion": "Highlight eco-friendly options",
            },
            "addictive_design_vs_health": {
                "keywords": ["addictive", "habit-forming", "sticky"],
                "user_value": ValueType.HEALTH,
                "suggestion": "Add wellness features, usage limits",
            },
        }

        user_primary = set(user_values.get("primary_values", []))
        rec_text = f"{recommendation.get('description', '')} {recommendation.get('terms', '')}"
        rec_text_lower = rec_text.lower()

        for pattern_name, pattern_data in conflict_patterns.items():
            user_value = pattern_data["user_value"]
            if user_value.value not in user_primary:
                continue

            keywords = pattern_data["keywords"]
            if any(kw.lower() in rec_text_lower for kw in keywords):
                conflicts.append({
                    "type": pattern_name,
                    "description": f"Recommendation contains '{keywords[0]}' which conflicts with user's {user_value.value} value",
                    "severity": AlignmentSeverity.MODERATE_CONFLICT.value,
                    "user_value": user_value.value,
                    "sales_pressure": sales_goal,
                    "recommendation": pattern_data["suggestion"],
                })

        return {
            "conflicts_detected": len(conflicts) > 0,
            "conflict_count": len(conflicts),
            "conflicts": conflicts,
            "ethical_path": ValuesAlignmentAgent._recommend_ethical_path(conflicts, user_values),
        }

    @staticmethod
    def _recommend_ethical_path(
        conflicts: List[Dict[str, Any]],
        user_values: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Recommend ethical path forward when conflicts exist."""

        if not conflicts:
            return {"recommendation": "proceed", "conditions": []}

        high_severity = any(
            c["severity"] == AlignmentSeverity.CRITICAL_CONFLICT.value
            for c in conflicts
        )

        if high_severity:
            return {
                "recommendation": "do_not_recommend",
                "reason": "Critical conflict with user values",
                "action": "Do not push this recommendation. Suggest alternatives that align better.",
            }

        moderate_conflicts = [c for c in conflicts if c["severity"] == AlignmentSeverity.MODERATE_CONFLICT.value]
        if len(moderate_conflicts) >= 2:
            return {
                "recommendation": "proceed_with_caution",
                "reason": f"Multiple moderate conflicts detected",
                "conditions": [c["recommendation"] for c in moderate_conflicts],
                "disclosure": "Be transparent about conflicts and trade-offs",
            }

        # Minor conflicts - proceed but address them
        return {
            "recommendation": "proceed_with_transparency",
            "reason": "Minor conflicts can be addressed with transparency",
            "conditions": [c["recommendation"] for c in conflicts],
            "action": "Acknowledge concerns and explain how to mitigate them",
        }

    @staticmethod
    def learn_alignment(
        recommendation_id: str,
        user_values: Dict[str, Any],
        actual_satisfaction: float,
        actual_value_alignment: float,
    ) -> Dict[str, Any]:
        """
        Learn from past recommendations to improve alignment.

        Tracks:
        - Recommendation alignment score vs actual satisfaction
        - Adjusts value weights based on outcomes
        """

        learning_record = {
            "recommendation_id": recommendation_id,
            "timestamp": datetime.utcnow().isoformat(),
            "predicted_alignment": 0,
            "actual_satisfaction": actual_satisfaction,
            "actual_alignment": actual_value_alignment,
            "prediction_error": 0,
            "value_adjustments": {},
        }

        # Calculate prediction error
        learning_record["prediction_error"] = abs(
            actual_satisfaction - learning_record["predicted_alignment"]
        )

        # If alignment was poor but satisfaction is high: adjust value extraction
        if actual_value_alignment < 0.5 and actual_satisfaction > 0.7:
            return {
                "learnings": "Values extraction may have missed implicit values",
                "action": "Request deeper value profiling in next interaction",
                "record": learning_record,
            }

        # If alignment was high but satisfaction is low: algorithm may have wrong weights
        if actual_value_alignment > 0.7 and actual_satisfaction < 0.5:
            return {
                "learnings": "Recommendation aligned but user still unsatisfied",
                "action": "May indicate missing values or incorrect weighting",
                "record": learning_record,
            }

        return {
            "learnings": "Prediction aligned with outcome",
            "action": "Continue monitoring",
            "record": learning_record,
        }

    @staticmethod
    def alignment_report(
        user_values: Dict[str, Any],
        recommendations: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Generate comprehensive alignment report."""

        scored_recommendations = [
            {
                **rec,
                "alignment": ValuesAlignmentAgent.score_recommendation_alignment(
                    rec, user_values
                ),
            }
            for rec in recommendations
        ]

        sorted_by_alignment = sorted(
            scored_recommendations,
            key=lambda x: x["alignment"]["alignment_score"],
            reverse=True,
        )

        return {
            "user_primary_values": user_values.get("primary_values", []),
            "total_recommendations": len(recommendations),
            "fully_aligned": sum(1 for r in scored_recommendations if r["alignment"]["alignment_score"] >= 80),
            "partially_aligned": sum(1 for r in scored_recommendations if 60 <= r["alignment"]["alignment_score"] < 80),
            "conflicted": sum(1 for r in scored_recommendations if r["alignment"]["alignment_score"] < 60),
            "ranked_by_alignment": scored_recommendations,
            "recommendation": "Prioritize fully aligned recommendations",
            "generated_at": datetime.utcnow().isoformat(),
        }
