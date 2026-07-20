"""
Comment Response Engine — Orchestrator that ties all response modules together.

Pipeline:
1. Analyze comment (sentiment, intent, urgency, audience)
2. Evaluate response options (humor, education, engagement)
3. Apply personality & authenticity checks
4. Optimize for engagement
5. Publish with tracking
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from .comment_analyzer import CommentAnalyzer
from .humor_generator import HumorGenerator
from .educational_responder import EducationalResponder
from .engagement_optimizer import EngagementOptimizer
from .personality_injector import PersonalityInjector

logger = logging.getLogger(__name__)


class CommentResponseEngine:
    """Orchestrates comment response generation."""

    def __init__(self, brand_personality: str = "founder"):
        """
        Initialize response engine.

        Args:
            brand_personality: "founder" | "expert" | "friend"
        """
        self.brand_personality = brand_personality
        self.response_history = []

    def generate_response(
        self,
        comment_text: str,
        author_profile: Dict[str, Any],
        post_context: Dict[str, Any],
        previous_comments: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate optimal response for comment.

        Complete pipeline:
        1. Analyze comment
        2. Score response types (humor, education, engagement)
        3. Select best approach
        4. Generate response
        5. Apply personality
        6. Optimize engagement
        7. Return with tracking

        Returns:
            {
                "response_text": str,
                "response_type": str,
                "confidence": 0-100,
                "engagement_score": 0-100,
                "priority": str,
                "tracking": {...},
            }
        """

        # Step 1: Comprehensive analysis
        analysis = CommentAnalyzer.comprehensive_analysis(
            comment_text,
            author_profile,
            post_context,
            previous_comments or [],
        )

        sentiment = analysis["sentiment"]
        intent = analysis["intent"]
        urgency = analysis["urgency"]
        audience = analysis["audience"]
        priority = analysis["overall_priority"]

        # Step 2: Score response approaches
        response_scores = self._score_response_approaches(
            sentiment, intent, audience, comment_text
        )

        # Step 3: Select best approach
        best_approach = max(response_scores.items(), key=lambda x: x[1]["score"])
        approach_type = best_approach[0]
        approach_score = best_approach[1]

        # Step 4: Generate response based on type
        if approach_type == "humor":
            response_result = self._generate_humor_response(
                sentiment, intent, comment_text, audience, approach_score
            )
        elif approach_type == "educational":
            response_result = self._generate_educational_response(
                comment_text, approach_score
            )
        elif approach_type == "engagement":
            response_result = self._generate_engagement_response(
                intent, audience, approach_score
            )
        else:
            response_result = self._generate_standard_response(
                sentiment, comment_text, approach_score
            )

        response_text = response_result.get("text", "")

        # Step 5: Apply personality
        personality_result = PersonalityInjector.inject_personality(
            response_text,
            self.brand_personality,
            variation_index=len(self.response_history) % 3,
        )
        response_text = personality_result["personalized"]

        # Step 6: Optimize engagement
        hook_result = EngagementOptimizer.craft_hook(comment_text, intent["intent"])
        cta_result = EngagementOptimizer.craft_cta(approach_type)

        final_response = f"{hook_result['hook']} {response_text}\n\n{cta_result['cta']}"

        # Calculate scores
        engagement_score = self._calculate_engagement_score(
            final_response, audience, approach_type
        )

        # Prepare response object
        response_object = {
            "response_text": final_response,
            "response_type": approach_type,
            "confidence": approach_score.get("confidence", 75),
            "engagement_score": engagement_score,
            "priority": priority,
            "analysis": {
                "sentiment": sentiment["sentiment"],
                "intent": intent["intent"],
                "urgency": urgency["urgency"],
                "audience_type": audience["primary_type"],
            },
            "tracking": {
                "comment_id": f"cmt_{hash(comment_text) % 10000}",
                "response_type": approach_type,
                "personality_applied": self.brand_personality,
                "timestamp": datetime.utcnow().isoformat(),
                "engagement_value": audience.get("engagement_value", "medium"),
                "author_id": author_profile.get("id", "unknown"),
            },
        }

        # Add to history for tracking
        self.response_history.append(response_object)

        return response_object

    def _score_response_approaches(
        self,
        sentiment: Dict,
        intent: Dict,
        audience: Dict,
        comment_text: str,
    ) -> Dict[str, Dict[str, float]]:
        """Score different response approaches."""

        scores = {
            "humor": {"score": 0, "confidence": 0},
            "educational": {"score": 0, "confidence": 0},
            "engagement": {"score": 0, "confidence": 0},
            "standard": {"score": 0, "confidence": 0},
        }

        # Humor scores high for praise + positive from engaged audience
        if sentiment["sentiment"] in ["positive", "very_positive"]:
            scores["humor"]["score"] += 30
            scores["humor"]["confidence"] = 85

        # Education scores high for questions
        if intent["intent"] == "question":
            scores["educational"]["score"] += 40
            scores["educational"]["confidence"] = 90

        # Engagement scores high for influencers/high-value
        if audience["engagement_value"] == "very_high":
            scores["engagement"]["score"] += 35
            scores["engagement"]["confidence"] = 80

        # Standard safe fallback
        scores["standard"]["score"] = 50
        scores["standard"]["confidence"] = 70

        return scores

    def _generate_humor_response(
        self,
        sentiment: Dict,
        intent: Dict,
        comment_text: str,
        audience: Dict,
        approach_score: Dict,
    ) -> Dict[str, Any]:
        """Generate humor-based response."""

        result = HumorGenerator.generate_humor_response(
            sentiment["sentiment"],
            intent["intent"],
            comment_text,
            audience["primary_type"],
        )

        return {
            "text": result.get("response", "Great observation!"),
            "type": "humor",
            "strength": result.get("strength", 70),
        }

    def _generate_educational_response(
        self,
        comment_text: str,
        approach_score: Dict,
    ) -> Dict[str, Any]:
        """Generate educational response."""

        result = EducationalResponder.create_educational_response(comment_text)

        return {
            "text": result["response_text"],
            "type": "educational",
            "resources": result.get("resources", []),
        }

    def _generate_engagement_response(
        self,
        intent: Dict,
        audience: Dict,
        approach_score: Dict,
    ) -> Dict[str, Any]:
        """Generate engagement-focused response."""

        hook = EngagementOptimizer.craft_hook("", intent.get("intent", "question"))

        return {
            "text": hook.get("hook", "Great point!"),
            "type": "engagement",
            "engagement_score": hook.get("engagement_score", 70),
        }

    def _generate_standard_response(
        self,
        sentiment: Dict,
        comment_text: str,
        approach_score: Dict,
    ) -> Dict[str, Any]:
        """Generate standard professional response."""

        if sentiment["sentiment"] in ["positive", "very_positive"]:
            text = "Thank you! We really appreciate your feedback."
        elif sentiment["sentiment"] in ["negative", "very_negative"]:
            text = "Thanks for the feedback. We're always looking to improve."
        else:
            text = "Great question! Let us know if you need more details."

        return {
            "text": text,
            "type": "standard",
        }

    def _calculate_engagement_score(
        self,
        response_text: str,
        audience: Dict,
        response_type: str,
    ) -> int:
        """Calculate predicted engagement score."""

        score = 50

        # Audience value boost
        if audience.get("engagement_value") == "very_high":
            score += 20
        elif audience.get("engagement_value") == "high":
            score += 10

        # Response type boost
        if response_type == "humor":
            score += 15
        elif response_type == "educational":
            score += 10

        # Length check (sweet spot: 100-200 words)
        words = len(response_text.split())
        if 100 <= words <= 200:
            score += 5
        elif words < 50:
            score -= 5

        return min(100, score)

    def get_analytics(self) -> Dict[str, Any]:
        """Get analytics on responses generated."""

        if not self.response_history:
            return {"total_responses": 0}

        total = len(self.response_history)
        avg_engagement = sum(r["engagement_score"] for r in self.response_history) / total
        avg_confidence = sum(r["confidence"] for r in self.response_history) / total

        response_types = {}
        for r in self.response_history:
            rt = r["response_type"]
            response_types[rt] = response_types.get(rt, 0) + 1

        return {
            "total_responses": total,
            "avg_engagement_score": round(avg_engagement, 1),
            "avg_confidence": round(avg_confidence, 1),
            "response_type_distribution": response_types,
            "most_common_type": max(response_types, key=response_types.get) if response_types else "unknown",
        }
