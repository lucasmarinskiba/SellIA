"""
Stage 1: Context Recall - Conversation Memory & Intent Detection

Features:
- Conversation memory (last 10 messages)
- User profile memory (preferences, history)
- Context retrieval (relevant prior exchanges)
- Sentiment tracking (user mood)
- Intent detection (what user wants)
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
from collections import defaultdict
import re


class Intent(str, Enum):
    """User intent types"""
    BUYING = "buying"
    SELLING = "selling"
    INFORMATION = "information"
    SUPPORT = "support"
    COMPLAINT = "complaint"
    FEEDBACK = "feedback"
    NEGOTIATION = "negotiation"
    UNKNOWN = "unknown"


class Sentiment(str, Enum):
    """User sentiment"""
    VERY_NEGATIVE = "very_negative"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    POSITIVE = "positive"
    VERY_POSITIVE = "very_positive"


@dataclass
class ConversationTurn:
    """Single conversation exchange"""
    timestamp: datetime
    user_message: str
    bot_response: str
    user_sentiment: Sentiment
    detected_intent: Intent
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UserProfile:
    """Persistent user profile"""
    user_id: str
    name: str
    email: Optional[str] = None
    industry: Optional[str] = None
    preferences: Dict[str, Any] = field(default_factory=dict)
    purchase_history: List[str] = field(default_factory=list)
    conversation_count: int = 0
    last_interaction: Optional[datetime] = None
    custom_traits: Dict[str, Any] = field(default_factory=dict)


class SentimentAnalyzer:
    """Detect user sentiment from messages"""

    POSITIVE_WORDS = {
        "love", "great", "awesome", "fantastic", "amazing", "wonderful",
        "excellent", "perfect", "brilliant", "thank", "thanks", "grateful",
        "happy", "excited", "pleased", "satisfied", "recommend"
    }

    NEGATIVE_WORDS = {
        "hate", "terrible", "awful", "horrible", "bad", "worst", "useless",
        "waste", "disappointed", "angry", "frustrated", "annoyed", "upset",
        "broken", "problem", "issue", "bug", "error", "fail", "refund"
    }

    VERY_NEGATIVE_WORDS = {
        "scam", "fraud", "criminal", "sue", "lawsuit", "cancel", "never",
        "destroy", "worst", "unacceptable"
    }

    @staticmethod
    def analyze(text: str) -> Sentiment:
        """Analyze sentiment from text"""
        text_lower = text.lower()

        # Count sentiment words
        very_negative_count = sum(1 for word in SentimentAnalyzer.VERY_NEGATIVE_WORDS
                                  if word in text_lower)
        negative_count = sum(1 for word in SentimentAnalyzer.NEGATIVE_WORDS
                            if word in text_lower)
        positive_count = sum(1 for word in SentimentAnalyzer.POSITIVE_WORDS
                            if word in text_lower)

        # Exclamation marks indicate intensity
        excitement = text.count('!') - text.count('?')

        # Determine sentiment
        if very_negative_count > 0:
            return Sentiment.VERY_NEGATIVE
        elif negative_count >= 2 or (negative_count == 1 and excitement < 0):
            return Sentiment.NEGATIVE
        elif positive_count >= 2 or (positive_count == 1 and excitement > 1):
            return Sentiment.VERY_POSITIVE if excitement > 2 else Sentiment.POSITIVE
        elif positive_count > 0:
            return Sentiment.POSITIVE
        elif negative_count > 0:
            return Sentiment.NEGATIVE

        return Sentiment.NEUTRAL


class IntentDetector:
    """Detect user intent from message"""

    BUYING_KEYWORDS = {
        "buy", "purchase", "order", "get", "want", "need", "price",
        "cost", "how much", "buy now", "interested", "available"
    }

    SELLING_KEYWORDS = {
        "sell", "sale", "discount", "offer", "deal", "sale price",
        "selling", "want to sell", "selling price"
    }

    SUPPORT_KEYWORDS = {
        "help", "support", "problem", "issue", "broken", "not working",
        "error", "bug", "crash", "fix", "troubleshoot", "technical"
    }

    COMPLAINT_KEYWORDS = {
        "complaint", "complain", "disappointed", "unsatisfied", "refund",
        "return", "exchange", "wrong", "damaged", "missing"
    }

    INFORMATION_KEYWORDS = {
        "what", "how", "why", "when", "where", "explain", "tell me",
        "information", "details", "describe", "specs"
    }

    NEGOTIATION_KEYWORDS = {
        "discount", "lower", "cheaper", "negotiate", "deal", "offer",
        "bulk", "wholesale", "volume", "minimum"
    }

    @staticmethod
    def detect(text: str) -> Intent:
        """Detect primary intent"""
        text_lower = text.lower()

        # Count keyword matches
        scores = {
            Intent.BUYING: sum(1 for kw in IntentDetector.BUYING_KEYWORDS
                              if kw in text_lower),
            Intent.SELLING: sum(1 for kw in IntentDetector.SELLING_KEYWORDS
                               if kw in text_lower),
            Intent.SUPPORT: sum(1 for kw in IntentDetector.SUPPORT_KEYWORDS
                               if kw in text_lower),
            Intent.COMPLAINT: sum(1 for kw in IntentDetector.COMPLAINT_KEYWORDS
                                 if kw in text_lower),
            Intent.INFORMATION: sum(1 for kw in IntentDetector.INFORMATION_KEYWORDS
                                   if kw in text_lower),
            Intent.NEGOTIATION: sum(1 for kw in IntentDetector.NEGOTIATION_KEYWORDS
                                   if kw in text_lower),
        }

        # Return highest scoring intent
        best_intent = max(scores, key=scores.get)
        return best_intent if scores[best_intent] > 0 else Intent.UNKNOWN


class ConversationMemory:
    """Manage conversation history for context"""

    def __init__(self, max_history: int = 10):
        self.history: Dict[str, List[ConversationTurn]] = defaultdict(list)
        self.max_history = max_history
        self.user_profiles: Dict[str, UserProfile] = {}

    def add_turn(
        self,
        user_id: str,
        user_message: str,
        bot_response: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ConversationTurn:
        """Add conversation turn"""
        sentiment = SentimentAnalyzer.analyze(user_message)
        intent = IntentDetector.detect(user_message)

        turn = ConversationTurn(
            timestamp=datetime.utcnow(),
            user_message=user_message,
            bot_response=bot_response,
            user_sentiment=sentiment,
            detected_intent=intent,
            metadata=metadata or {}
        )

        # Keep only recent history
        self.history[user_id].append(turn)
        if len(self.history[user_id]) > self.max_history:
            self.history[user_id] = self.history[user_id][-self.max_history:]

        # Update user profile
        self._update_profile(user_id, sentiment, intent)

        return turn

    def _update_profile(self, user_id: str, sentiment: Sentiment, intent: Intent) -> None:
        """Update user profile based on interaction"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = UserProfile(user_id=user_id, name=user_id)

        profile = self.user_profiles[user_id]
        profile.conversation_count += 1
        profile.last_interaction = datetime.utcnow()

        # Track preferences
        if "sentiments" not in profile.preferences:
            profile.preferences["sentiments"] = {}
        profile.preferences["sentiments"][sentiment.value] = \
            profile.preferences["sentiments"].get(sentiment.value, 0) + 1

        if "intents" not in profile.preferences:
            profile.preferences["intents"] = {}
        profile.preferences["intents"][intent.value] = \
            profile.preferences["intents"].get(intent.value, 0) + 1

    def get_history(self, user_id: str, limit: Optional[int] = None) -> List[ConversationTurn]:
        """Get conversation history"""
        history = self.history[user_id]
        if limit:
            return history[-limit:]
        return history

    def get_context_summary(self, user_id: str) -> Dict[str, Any]:
        """Get summary of recent context"""
        history = self.get_history(user_id, limit=5)
        if not history:
            return {}

        # Get most recent intent and sentiment
        recent_intent = history[-1].detected_intent if history else Intent.UNKNOWN
        recent_sentiment = history[-1].user_sentiment if history else Sentiment.NEUTRAL

        # Summarize topics
        all_messages = ' '.join([turn.user_message for turn in history])

        return {
            "last_intent": recent_intent.value,
            "last_sentiment": recent_sentiment.value,
            "message_count": len(history),
            "topics": self._extract_topics(all_messages),
            "recent_exchanges": [
                {
                    "user": turn.user_message[:100],
                    "bot": turn.bot_response[:100],
                    "intent": turn.detected_intent.value,
                    "sentiment": turn.user_sentiment.value,
                }
                for turn in history[-3:]
            ]
        }

    def _extract_topics(self, text: str) -> List[str]:
        """Extract main topics from text"""
        # Simple keyword extraction
        keywords = {}
        words = re.findall(r'\b\w{4,}\b', text.lower())

        common_words = {
            "this", "that", "with", "have", "from", "been", "their",
            "which", "these", "would", "could", "should"
        }

        for word in words:
            if word not in common_words and len(word) > 3:
                keywords[word] = keywords.get(word, 0) + 1

        # Return top keywords as topics
        return sorted(keywords.keys(), key=lambda x: keywords[x], reverse=True)[:5]

    def get_user_profile(self, user_id: str) -> UserProfile:
        """Get or create user profile"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = UserProfile(user_id=user_id, name=user_id)
        return self.user_profiles[user_id]

    def update_profile(self, user_id: str, **kwargs) -> UserProfile:
        """Update user profile fields"""
        profile = self.get_user_profile(user_id)
        for key, value in kwargs.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        return profile


class ContextRetriever:
    """Retrieve relevant context for response generation"""

    def __init__(self, memory: ConversationMemory):
        self.memory = memory

    def get_context(self, user_id: str, current_message: str) -> Dict[str, Any]:
        """Get all relevant context for response generation"""
        profile = self.memory.get_user_profile(user_id)
        history = self.memory.get_history(user_id, limit=5)

        current_sentiment = SentimentAnalyzer.analyze(current_message)
        current_intent = IntentDetector.detect(current_message)

        return {
            "user_profile": {
                "name": profile.name,
                "conversation_count": profile.conversation_count,
                "primary_intent": self._get_primary_intent(profile),
                "overall_sentiment": self._get_overall_sentiment(profile),
            },
            "current_message": {
                "intent": current_intent.value,
                "sentiment": current_sentiment.value,
            },
            "conversation_history": [
                {
                    "user": turn.user_message,
                    "bot": turn.bot_response,
                    "sentiment": turn.user_sentiment.value,
                    "intent": turn.detected_intent.value,
                }
                for turn in history
            ],
            "topics_of_interest": self._extract_user_topics(profile),
            "response_guidance": self._generate_guidance(
                current_intent, current_sentiment, profile
            )
        }

    def _get_primary_intent(self, profile: UserProfile) -> str:
        """Get user's primary intent"""
        intents = profile.preferences.get("intents", {})
        if not intents:
            return "unknown"
        return max(intents, key=intents.get)

    def _get_overall_sentiment(self, profile: UserProfile) -> str:
        """Get user's overall sentiment"""
        sentiments = profile.preferences.get("sentiments", {})
        if not sentiments:
            return "neutral"
        return max(sentiments, key=sentiments.get)

    def _extract_user_topics(self, profile: UserProfile) -> List[str]:
        """Extract user's topics of interest"""
        return profile.preferences.get("topics", [])

    def _generate_guidance(
        self,
        intent: Intent,
        sentiment: Sentiment,
        profile: UserProfile
    ) -> Dict[str, Any]:
        """Generate guidance for response generation"""
        guidance = {
            "tone": "friendly",
            "formality": 0.5,
            "urgency": False,
            "offer_help": False,
            "suggest_action": False,
        }

        # Adjust based on sentiment
        if sentiment in [Sentiment.VERY_NEGATIVE, Sentiment.NEGATIVE]:
            guidance["tone"] = "empathetic"
            guidance["offer_help"] = True
        elif sentiment == Sentiment.VERY_POSITIVE:
            guidance["tone"] = "enthusiastic"

        # Adjust based on intent
        if intent == Intent.BUYING:
            guidance["suggest_action"] = True
            guidance["urgency"] = True
        elif intent == Intent.COMPLAINT:
            guidance["offer_help"] = True
            guidance["tone"] = "apologetic"

        # Adjust based on conversation history
        if profile.conversation_count < 3:
            guidance["formality"] = 0.6  # More formal with new users
        elif profile.conversation_count > 10:
            guidance["formality"] = 0.3  # More casual with regulars

        return guidance


# Singleton instances
_memory_instance: Optional[ConversationMemory] = None
_retriever_instance: Optional[ContextRetriever] = None


def get_conversation_memory() -> ConversationMemory:
    """Get or create memory singleton"""
    global _memory_instance
    if _memory_instance is None:
        _memory_instance = ConversationMemory()
    return _memory_instance


def get_context_retriever() -> ContextRetriever:
    """Get or create retriever singleton"""
    global _retriever_instance
    if _retriever_instance is None:
        memory = get_conversation_memory()
        _retriever_instance = ContextRetriever(memory)
    return _retriever_instance
