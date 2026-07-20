"""
Educational Responder — Micro-teaching, resources, FAQ integration.
"""

import logging
from typing import Dict, List, Any, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class ContentType(str, Enum):
    """Educational content types."""
    TUTORIAL = "tutorial"
    DOCUMENTATION = "documentation"
    BLOG_ARTICLE = "blog_article"
    VIDEO = "video"
    FAQ = "faq"
    CASE_STUDY = "case_study"


class EducationalResponder:
    """Provides educational responses with resources."""

    # FAQ Database (topic -> [questions] -> [answers])
    FAQ_DATABASE = {
        "pricing": {
            "How much does it cost?": "Pricing starts at $29/month. See full breakdown.",
            "Do you offer discounts?": "Yes, annual billing saves 20%. Non-profits get 50% off.",
            "Money-back guarantee?": "30-day guarantee. No questions asked refunds.",
        },
        "integration": {
            "Do you integrate with Zapier?": "Yes! 100+ native integrations via Zapier.",
            "API available?": "Full REST API. GraphQL beta available.",
            "How long to integrate?": "Most integrations take <1 hour. We have guides.",
        },
        "features": {
            "Can I customize this?": "Yes, all plans are fully customizable.",
            "What features are included?": "Full feature list at [link]",
            "Can I try it free?": "14-day free trial, no credit card required.",
        },
    }

    # Learning paths
    LEARNING_PATHS = {
        "beginner": [
            "Getting Started (10 min video)",
            "Feature Overview (blog post)",
            "Your First Setup (interactive tutorial)",
            "Common Tasks (FAQ + examples)",
        ],
        "intermediate": [
            "Advanced Features (docs)",
            "Custom Workflows (video series)",
            "Performance Optimization (blog)",
            "Integration Guide (docs + examples)",
        ],
        "advanced": [
            "API Reference (complete docs)",
            "Custom Development (technical docs)",
            "Architecture Deep Dive (video)",
            "Case Studies (real-world examples)",
        ],
    }

    @staticmethod
    def analyze_question(question_text: str) -> Dict[str, Any]:
        """
        Analyze question to identify learning need.

        Returns:
            {
                "topic": str,
                "skill_level": "beginner" | "intermediate" | "advanced",
                "urgency": "low" | "high",
                "best_resource_type": ContentType,
            }
        """

        question_lower = question_text.lower()

        # Topic detection
        topics = {
            "pricing": ["cost", "price", "fee", "expensive", "discount", "refund"],
            "integration": ["integrate", "connect", "api", "zapier", "plugin", "webhook"],
            "features": ["feature", "does it", "can i", "how to", "work with"],
            "setup": ["setup", "install", "configure", "start", "begin"],
        }

        topic = "general"
        for t, keywords in topics.items():
            if any(kw in question_lower for kw in keywords):
                topic = t
                break

        # Skill level detection
        if "beginner" in question_lower or "start" in question_lower:
            skill_level = "beginner"
        elif "advanced" in question_lower or "custom" in question_lower:
            skill_level = "advanced"
        else:
            skill_level = "intermediate"

        # Urgency
        urgent_words = ["urgent", "asap", "now", "immediately", "broken", "error"]
        urgency = "high" if any(w in question_lower for w in urgent_words) else "low"

        # Best resource type
        if skill_level == "beginner":
            resource_type = ContentType.VIDEO
        elif "why" in question_lower or "explain" in question_lower:
            resource_type = ContentType.BLOG_ARTICLE
        elif "how" in question_lower:
            resource_type = ContentType.TUTORIAL
        else:
            resource_type = ContentType.DOCUMENTATION

        return {
            "topic": topic,
            "skill_level": skill_level,
            "urgency": urgency,
            "best_resource_type": resource_type.value,
            "confidence": 85,
        }

    @staticmethod
    def extract_learning_goals(question_text: str) -> List[str]:
        """Extract what user wants to learn."""

        goals = []
        patterns = {
            "how_to": ["how to", "how do i", "how can i"],
            "understanding": ["why", "explain", "understand", "what"],
            "troubleshooting": ["error", "broken", "doesn't work", "problem"],
            "best_practices": ["best way", "recommended", "should i"],
        }

        question_lower = question_text.lower()
        for goal_type, keywords in patterns.items():
            if any(kw in question_lower for kw in keywords):
                goals.append(goal_type)

        return goals

    @staticmethod
    def find_relevant_faq(question_text: str) -> Dict[str, Any]:
        """
        Find relevant FAQ entries for question.

        Returns:
            {
                "found": bool,
                "faq_matches": [{question, answer}, ...],
                "exact_match": bool,
                "relevance_score": 0-100,
            }
        """

        question_lower = question_text.lower()
        faq_matches = []
        best_score = 0

        for category, faq_items in EducationalResponder.FAQ_DATABASE.items():
            for faq_q, faq_a in faq_items.items():
                # Calculate relevance
                words_in_question = set(question_lower.split())
                words_in_faq = set(faq_q.lower().split())
                overlap = len(words_in_question & words_in_faq)
                score = (overlap / len(words_in_question)) * 100 if words_in_question else 0

                if score > 40:
                    faq_matches.append({
                        "category": category,
                        "question": faq_q,
                        "answer": faq_a,
                        "relevance_score": int(score),
                    })
                    best_score = max(best_score, score)

        faq_matches.sort(key=lambda x: x["relevance_score"], reverse=True)

        return {
            "found": len(faq_matches) > 0,
            "faq_matches": faq_matches[:3],
            "exact_match": best_score >= 80,
            "relevance_score": int(best_score),
        }

    @staticmethod
    def generate_learning_path(skill_level: str, topic: str) -> Dict[str, Any]:
        """
        Generate personalized learning path.

        Returns:
            {
                "path": [list of resources],
                "estimated_time": str,
                "description": str,
            }
        """

        base_path = EducationalResponder.LEARNING_PATHS.get(skill_level, [])

        # Filter/customize for topic
        if topic == "pricing":
            path = ["Pricing Overview", "Plan Comparison", "ROI Calculator"]
            time = "5-10 minutes"
        elif topic == "integration":
            path = ["Integration Guide", "API Documentation", "Example Workflows"]
            time = "30 minutes - 1 hour"
        elif topic == "setup":
            path = ["Quick Start (5 min)", "Configuration Guide", "First Workflow"]
            time = "15-30 minutes"
        else:
            path = base_path
            time = "30 minutes - 2 hours"

        return {
            "path": path,
            "estimated_time": time,
            "description": f"Learning path for {skill_level} users learning about {topic}",
            "difficulty": skill_level,
        }

    @staticmethod
    def create_educational_response(
        question_text: str,
        skill_level: str = "intermediate",
    ) -> Dict[str, Any]:
        """
        Create complete educational response.

        Returns:
            {
                "response_text": str,
                "resources": [list],
                "learning_path": Dict,
                "faq_reference": Dict or None,
                "confidence": 0-100,
            }
        """

        analysis = EducationalResponder.analyze_question(question_text)
        faq_result = EducationalResponder.find_relevant_faq(question_text)
        learning_path = EducationalResponder.generate_learning_path(
            skill_level or analysis["skill_level"],
            analysis["topic"],
        )

        # Build response text
        response_text = ""
        if faq_result["exact_match"]:
            faq_answer = faq_result["faq_matches"][0]["answer"]
            response_text = f"Great question! {faq_answer}\n\n"

        response_text += (
            f"To dive deeper, here's a learning path for {analysis['skill_level']} users:\n"
            + "\n".join(f"• {item}" for item in learning_path["path"])
        )

        return {
            "response_text": response_text,
            "topic": analysis["topic"],
            "skill_level": analysis["skill_level"],
            "resources": [
                {
                    "type": analysis["best_resource_type"],
                    "title": item,
                    "estimated_time": learning_path["estimated_time"],
                }
                for item in learning_path["path"]
            ],
            "faq_reference": faq_result["faq_matches"][0] if faq_result["found"] else None,
            "learning_path": learning_path,
            "confidence": min(100, faq_result.get("relevance_score", 50) + 25),
        }

    @staticmethod
    def suggest_resources(topic: str, skill_level: str) -> List[Dict[str, Any]]:
        """Suggest best resources for topic."""

        resources = {
            "pricing": [
                {"type": "faq", "title": "Pricing FAQ", "url": "/faq/pricing"},
                {"type": "blog", "title": "ROI Calculator", "url": "/blog/roi"},
                {"type": "comparison", "title": "Plan Comparison", "url": "/pricing"},
            ],
            "integration": [
                {"type": "docs", "title": "API Docs", "url": "/docs/api"},
                {"type": "tutorial", "title": "Integration Guide", "url": "/guides/integration"},
                {"type": "video", "title": "Zapier Setup", "url": "/videos/zapier"},
            ],
            "features": [
                {"type": "docs", "title": "Feature Overview", "url": "/docs/features"},
                {"type": "blog", "title": "Feature Spotlight", "url": "/blog/features"},
                {"type": "video", "title": "Feature Tour", "url": "/videos/tour"},
            ],
        }

        return resources.get(topic, [])
