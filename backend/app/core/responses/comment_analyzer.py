"""
Comment Analyzer — Sentiment, intent, urgency, audience type extraction.

Analyzes incoming comments to understand:
1. Sentiment (positive/negative/neutral/mixed)
2. Intent (question/praise/criticism/joke/request)
3. Urgency (low/medium/high/critical)
4. Audience type (influencer/competitor/fan/troll/decision-maker)
5. Context (previous comments, user history, engagement pattern)
"""

import logging
from typing import Dict, List, Any, Tuple
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class Sentiment(str, Enum):
    """Comment sentiment."""
    VERY_POSITIVE = "very_positive"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    VERY_NEGATIVE = "very_negative"


class Intent(str, Enum):
    """Comment intent."""
    QUESTION = "question"
    PRAISE = "praise"
    CRITICISM = "criticism"
    JOKE = "joke"
    REQUEST = "request"
    SUGGESTION = "suggestion"
    CONCERN = "concern"


class AudienceType(str, Enum):
    """Comment author type."""
    INFLUENCER = "influencer"  # High reach
    COMPETITOR = "competitor"  # Selling similar
    FAN = "fan"  # Supporter
    TROLL = "troll"  # Antagonistic
    DECISION_MAKER = "decision_maker"  # Buyer
    CURIOUS = "curious"  # Interested but not yet decided


class UrgencyLevel(str, Enum):
    """Urgency of response."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CommentAnalyzer:
    """Analyzes comments in depth."""

    # Sentiment indicators
    POSITIVE_KEYWORDS = [
        "love", "amazing", "awesome", "great", "excellent", "brilliant",
        "fantastic", "wonderful", "perfect", "helped", "saved", "grateful",
        "thanks", "thank you", "recommend", "best", "beautiful", "impressed",
    ]

    NEGATIVE_KEYWORDS = [
        "hate", "terrible", "awful", "bad", "poor", "disappointed",
        "waste", "scam", "broken", "useless", "fail", "problem",
        "issue", "error", "can't", "won't", "doesn't work",
    ]

    # Intent indicators
    INTENT_PATTERNS = {
        Intent.QUESTION: [
            r"\?$", "how", "what", "when", "where", "why", "can you",
            "is it", "does it", "would", "could", "should",
        ],
        Intent.PRAISE: [
            "love", "great", "awesome", "amazing", "excellent", "thank",
            "appreciate", "grateful", "impressed", "brilliant",
        ],
        Intent.CRITICISM: [
            "not good", "bad", "poor", "terrible", "awful", "disappointed",
            "waste", "doesn't work", "issue", "problem", "hate",
        ],
        Intent.JOKE: [
            "lol", "haha", "😂", ";)", "rofl", "just kidding", "just joking",
        ],
        Intent.REQUEST: [
            "can you", "could you", "would you", "please", "need", "want",
            "would like", "looking for", "help", "advice",
        ],
    }

    # Audience type indicators
    AUDIENCE_INDICATORS = {
        AudienceType.INFLUENCER: {
            "keywords": ["followers", "followers", "my audience", "my platform"],
            "metrics": {"followers": 10000, "engagement_rate": 0.02},
        },
        AudienceType.COMPETITOR: {
            "keywords": ["we do", "our product", "our solution", "we offer"],
            "patterns": ["comparison", "alternative", "vs"],
        },
        AudienceType.DECISION_MAKER: {
            "keywords": ["budget", "implementation", "timeline", "pricing", "contract"],
            "patterns": ["ROI", "enterprise", "scale", "team"],
        },
        AudienceType.TROLL: {
            "keywords": ["stupid", "dumb", "idiot", "pathetic", "worst"],
            "patterns": ["personal attack", "no constructive criticism"],
        },
    }

    # Urgency indicators
    URGENCY_KEYWORDS = {
        UrgencyLevel.CRITICAL: ["urgent", "emergency", "asap", "dying", "broken now"],
        UrgencyLevel.HIGH: ["soon", "quickly", "important", "need help", "stuck"],
        UrgencyLevel.MEDIUM: ["interested", "considering", "thinking"],
        UrgencyLevel.LOW: ["just wondering", "curious", "maybe later"],
    }

    @staticmethod
    def analyze_sentiment(comment_text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of comment.

        Returns:
            {
                "sentiment": Sentiment,
                "score": -1.0 to 1.0,
                "positive_indicators": [list],
                "negative_indicators": [list],
                "confidence": 0-100,
            }
        """

        text_lower = comment_text.lower()
        positive_count = sum(1 for keyword in CommentAnalyzer.POSITIVE_KEYWORDS
                           if keyword in text_lower)
        negative_count = sum(1 for keyword in CommentAnalyzer.NEGATIVE_KEYWORDS
                           if keyword in text_lower)

        total_keywords = positive_count + negative_count
        score = 0

        if total_keywords > 0:
            score = (positive_count - negative_count) / total_keywords
        else:
            score = 0

        # Determine sentiment
        if score > 0.6:
            sentiment = Sentiment.VERY_POSITIVE
        elif score > 0.2:
            sentiment = Sentiment.POSITIVE
        elif score > -0.2:
            sentiment = Sentiment.NEUTRAL
        elif score > -0.6:
            sentiment = Sentiment.NEGATIVE
        else:
            sentiment = Sentiment.VERY_NEGATIVE

        confidence = min(100, (total_keywords * 15))

        return {
            "sentiment": sentiment.value,
            "score": round(score, 2),
            "positive_indicators": [kw for kw in CommentAnalyzer.POSITIVE_KEYWORDS
                                    if kw in text_lower],
            "negative_indicators": [kw for kw in CommentAnalyzer.NEGATIVE_KEYWORDS
                                    if kw in text_lower],
            "confidence": confidence,
        }

    @staticmethod
    def analyze_intent(comment_text: str) -> Dict[str, Any]:
        """
        Analyze primary intent of comment.

        Returns:
            {
                "intent": Intent,
                "confidence": 0-100,
                "secondary_intents": [list],
            }
        """

        text_lower = comment_text.lower()
        intent_scores = {}

        for intent, patterns in CommentAnalyzer.INTENT_PATTERNS.items():
            score = sum(1 for pattern in patterns
                       if pattern.lower() in text_lower or text_lower.endswith("?"))
            intent_scores[intent] = score

        primary_intent = max(intent_scores, key=intent_scores.get)
        primary_score = intent_scores[primary_intent]

        # Get secondary intents
        sorted_intents = sorted(intent_scores.items(), key=lambda x: x[1], reverse=True)
        secondary_intents = [intent.value for intent, _ in sorted_intents[1:3]
                            if intent_scores[intent] > 0]

        confidence = min(100, primary_score * 25)

        return {
            "intent": primary_intent.value,
            "confidence": confidence,
            "secondary_intents": secondary_intents,
            "intent_score": primary_score,
        }

    @staticmethod
    def analyze_urgency(comment_text: str, user_history: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze urgency of response needed.

        Returns:
            {
                "urgency": UrgencyLevel,
                "score": 0-100,
                "indicators": [list],
            }
        """

        text_lower = comment_text.lower()
        urgency_scores = {}

        for level, keywords in CommentAnalyzer.URGENCY_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            urgency_scores[level] = score

        primary_urgency = max(urgency_scores, key=urgency_scores.get)

        # Boost urgency if user is high-value
        if user_history:
            if user_history.get("is_buyer"):
                primary_urgency = (
                    UrgencyLevel.CRITICAL if urgency_scores[primary_urgency] > 0
                    else primary_urgency
                )
            if user_history.get("engagement_rate", 0) > 0.1:  # High engagement
                if primary_urgency == UrgencyLevel.MEDIUM:
                    primary_urgency = UrgencyLevel.HIGH

        score = urgency_scores.get(primary_urgency, 0) * 25

        indicators = []
        for level, keywords in CommentAnalyzer.URGENCY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    indicators.append(keyword)
                    break

        return {
            "urgency": primary_urgency.value,
            "score": min(100, score),
            "indicators": indicators,
        }

    @staticmethod
    def identify_audience_type(
        author_profile: Dict[str, Any],
        comment_text: str,
    ) -> Dict[str, Any]:
        """
        Identify what type of audience member this is.

        Returns:
            {
                "primary_type": AudienceType,
                "confidence": 0-100,
                "secondary_types": [list],
                "traits": {description of traits},
            }
        """

        text_lower = comment_text.lower()
        type_scores = {at: 0 for at in AudienceType}

        # Analyze comment text
        for audience_type, indicators in CommentAnalyzer.AUDIENCE_INDICATORS.items():
            keywords = indicators.get("keywords", [])
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    type_scores[audience_type] += 1

        # Analyze profile
        follower_count = author_profile.get("followers", 0)
        engagement_rate = author_profile.get("engagement_rate", 0)

        if follower_count > 100000:
            type_scores[AudienceType.INFLUENCER] += 3
        if author_profile.get("is_competitor"):
            type_scores[AudienceType.COMPETITOR] += 3
        if author_profile.get("is_buyer"):
            type_scores[AudienceType.DECISION_MAKER] += 2
        if author_profile.get("engagement_history", 0) > 10:
            type_scores[AudienceType.FAN] += 2

        primary_type = max(type_scores, key=type_scores.get)
        confidence = min(100, type_scores[primary_type] * 20)

        # Default to curious if no strong indicator
        if confidence < 30:
            primary_type = AudienceType.CURIOUS
            confidence = 50

        secondary_types = [at.value for at, score in sorted(type_scores.items(),
                                                           key=lambda x: x[1], reverse=True)[1:3]
                          if type_scores[at] > 0]

        traits = CommentAnalyzer._get_audience_traits(primary_type)

        return {
            "primary_type": primary_type.value,
            "confidence": confidence,
            "secondary_types": secondary_types,
            "traits": traits,
            "engagement_value": CommentAnalyzer._calculate_engagement_value(
                primary_type, author_profile
            ),
        }

    @staticmethod
    def _get_audience_traits(audience_type: AudienceType) -> Dict[str, str]:
        """Get characteristics of audience type."""
        traits_map = {
            AudienceType.INFLUENCER: "High reach, can amplify message, value relationship",
            AudienceType.COMPETITOR: "Comparing products, may want to learn about yours",
            AudienceType.FAN: "Supporter, engaged, good for testimonials",
            AudienceType.TROLL: "Antagonistic, respond briefly and professionally",
            AudienceType.DECISION_MAKER: "Evaluating ROI, address business metrics",
            AudienceType.CURIOUS: "Learning, provide educational content",
        }
        return traits_map.get(audience_type, "Unknown type")

    @staticmethod
    def _calculate_engagement_value(audience_type: AudienceType, profile: Dict[str, Any]) -> str:
        """Calculate value of engaging with this comment."""
        if audience_type == AudienceType.INFLUENCER:
            return "very_high"  # Potential reach
        elif audience_type == AudienceType.DECISION_MAKER:
            return "high"  # Potential sale
        elif audience_type == AudienceType.FAN:
            return "medium"  # Good for social proof
        elif audience_type == AudienceType.CURIOUS:
            return "medium"  # Potential customer
        elif audience_type == AudienceType.COMPETITOR:
            return "low"  # Unlikely to convert
        else:  # Troll
            return "very_low"

    @staticmethod
    def extract_context(
        comment_text: str,
        author_profile: Dict[str, Any],
        post_context: Dict[str, Any],
        previous_comments: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Extract rich context about comment.

        Returns:
            {
                "mentions_specific_feature": bool,
                "specific_features": [list],
                "has_question": bool,
                "question_topics": [list],
                "related_previous_comments": [list],
                "sentiment_trend": str,
            }
        """

        text_lower = comment_text.lower()

        # Feature mentions
        specific_features = []
        feature_keywords = ["feature", "pricing", "integration", "api", "plugin", "support"]
        for keyword in feature_keywords:
            if keyword in text_lower:
                specific_features.append(keyword)

        # Questions
        has_question = "?" in comment_text
        question_topics = []
        if has_question:
            question_types = ["how", "what", "when", "where", "why"]
            for qtype in question_types:
                if qtype in text_lower:
                    question_topics.append(qtype)

        # Related previous comments
        related = []
        if previous_comments:
            for prev in previous_comments[-5:]:  # Last 5 comments
                prev_text_lower = prev.get("text", "").lower()
                # Simple similarity: shared words
                if any(word in text_lower for word in prev_text_lower.split()
                      if len(word) > 4):
                    related.append(prev)

        # Sentiment trend
        sentiment_trend = "neutral"
        if related:
            sentiments = [CommentAnalyzer.analyze_sentiment(c.get("text", ""))
                         for c in related[-3:]]
            avg_score = sum(s["score"] for s in sentiments) / len(sentiments)
            current_sentiment = CommentAnalyzer.analyze_sentiment(comment_text)["score"]

            if current_sentiment > avg_score:
                sentiment_trend = "improving"
            elif current_sentiment < avg_score:
                sentiment_trend = "deteriorating"

        return {
            "mentions_specific_feature": len(specific_features) > 0,
            "specific_features": specific_features,
            "has_question": has_question,
            "question_topics": question_topics,
            "related_previous_comments_count": len(related),
            "sentiment_trend": sentiment_trend,
            "post_type": post_context.get("type", "post"),
            "post_topic": post_context.get("topic", "general"),
        }

    @staticmethod
    def comprehensive_analysis(
        comment_text: str,
        author_profile: Dict[str, Any] = None,
        post_context: Dict[str, Any] = None,
        previous_comments: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Comprehensive comment analysis combining all checks.

        Returns complete analysis dict with all dimensions.
        """

        author_profile = author_profile or {}
        post_context = post_context or {}
        previous_comments = previous_comments or []

        sentiment = CommentAnalyzer.analyze_sentiment(comment_text)
        intent = CommentAnalyzer.analyze_intent(comment_text)
        urgency = CommentAnalyzer.analyze_urgency(comment_text, author_profile)
        audience = CommentAnalyzer.identify_audience_type(author_profile, comment_text)
        context = CommentAnalyzer.extract_context(
            comment_text, author_profile, post_context, previous_comments
        )

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "comment_text": comment_text[:500],  # Truncate for summary
            "sentiment": sentiment,
            "intent": intent,
            "urgency": urgency,
            "audience": audience,
            "context": context,
            "overall_priority": CommentAnalyzer._calculate_priority(
                sentiment, urgency, audience
            ),
        }

    @staticmethod
    def _calculate_priority(sentiment: Dict, urgency: Dict, audience: Dict) -> str:
        """Calculate overall response priority."""
        engagement_value = audience.get("engagement_value", "very_low")
        urgency_level = urgency.get("urgency", "low")
        sentiment_score = sentiment.get("score", 0)

        if engagement_value == "very_high" or urgency_level == "critical":
            return "critical"
        elif engagement_value == "high" and urgency_level in ["high", "critical"]:
            return "high"
        elif engagement_value in ["high", "medium"] and sentiment_score < -0.5:
            return "high"  # Negative from important person
        elif urgency_level in ["high", "critical"]:
            return "medium"
        elif engagement_value == "medium":
            return "medium"
        else:
            return "low"
