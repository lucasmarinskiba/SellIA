"""
Stage 1 Tests: Context Recall - Memory, Intent Detection, Sentiment Analysis

Test Coverage:
- Sentiment analysis (positive/negative/neutral)
- Intent detection (buying/selling/support/etc)
- Conversation memory management
- User profile tracking
- Context retrieval and summarization
"""

import pytest
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.core.response.context_recall import (
    SentimentAnalyzer, Sentiment, IntentDetector, Intent,
    ConversationMemory, UserProfile, ContextRetriever,
    ConversationTurn, get_conversation_memory, get_context_retriever
)


class TestSentimentAnalyzer:
    """Test sentiment analysis"""

    def test_positive_sentiment_detection(self):
        positive_texts = [
            "I love this product! It's amazing!",
            "Thank you so much, this is wonderful",
            "I'm so grateful and satisfied",
            "Excellent service, highly recommend",
        ]
        for text in positive_texts:
            sentiment = SentimentAnalyzer.analyze(text)
            assert sentiment in [Sentiment.POSITIVE, Sentiment.VERY_POSITIVE]

    def test_negative_sentiment_detection(self):
        negative_texts = [
            "This is terrible and broken",
            "I hate this, worst experience ever",
            "Very disappointed and frustrated",
            "This is useless waste of money",
        ]
        for text in negative_texts:
            sentiment = SentimentAnalyzer.analyze(text)
            assert sentiment in [Sentiment.NEGATIVE, Sentiment.VERY_NEGATIVE]

    def test_neutral_sentiment_detection(self):
        neutral_texts = [
            "This is a product",
            "It costs 100 dollars",
            "The weather is nice today",
        ]
        for text in neutral_texts:
            sentiment = SentimentAnalyzer.analyze(text)
            assert sentiment == Sentiment.NEUTRAL

    def test_very_positive_sentiment(self):
        text = "I LOVE this!!! It's absolutely amazing and fantastic!!!"
        sentiment = SentimentAnalyzer.analyze(text)
        assert sentiment == Sentiment.VERY_POSITIVE

    def test_very_negative_sentiment(self):
        text = "This is a scam! I'm going to sue! Criminal fraud!"
        sentiment = SentimentAnalyzer.analyze(text)
        assert sentiment == Sentiment.VERY_NEGATIVE

    def test_sentiment_with_exclamation_intensity(self):
        positive = "I like this"
        positive_excited = "I like this!!!!"
        s1 = SentimentAnalyzer.analyze(positive)
        s2 = SentimentAnalyzer.analyze(positive_excited)
        # Excited version should be detected
        assert s1 == Sentiment.NEUTRAL or s1 == Sentiment.POSITIVE
        assert s2 in [Sentiment.POSITIVE, Sentiment.VERY_POSITIVE]


class TestIntentDetector:
    """Test intent detection"""

    def test_buying_intent_detection(self):
        buying_texts = [
            "I want to buy this product",
            "How much does it cost?",
            "I'm interested in purchasing",
            "Can I order this now?",
            "What's the price?",
        ]
        for text in buying_texts:
            intent = IntentDetector.detect(text)
            assert intent in [Intent.BUYING, Intent.INFORMATION]

    def test_selling_intent_detection(self):
        selling_texts = [
            "I want to sell my product",
            "What's your sale price?",
            "I'm selling this at discount",
            "Wholesale offer available",
        ]
        for text in selling_texts:
            intent = IntentDetector.detect(text)
            assert intent in [Intent.SELLING, Intent.INFORMATION]

    def test_support_intent_detection(self):
        support_texts = [
            "I need help with this",
            "The app is broken, can you fix it?",
            "Technical support needed",
            "Getting an error, please help",
        ]
        for text in support_texts:
            intent = IntentDetector.detect(text)
            assert intent in [Intent.SUPPORT, Intent.COMPLAINT, Intent.INFORMATION]

    def test_complaint_intent_detection(self):
        complaint_texts = [
            "I want a refund, this is broken",
            "This product damaged, I need replacement",
            "I'm very disappointed, need refund",
        ]
        for text in complaint_texts:
            intent = IntentDetector.detect(text)
            assert intent in [Intent.COMPLAINT, Intent.SUPPORT]

    def test_information_intent_detection(self):
        info_texts = [
            "What is this product?",
            "Can you explain how it works?",
            "Tell me more about features",
        ]
        for text in info_texts:
            intent = IntentDetector.detect(text)
            assert intent in [Intent.INFORMATION, Intent.UNKNOWN]

    def test_negotiation_intent_detection(self):
        negotiation_texts = [
            "Can you lower the price?",
            "What's your bulk discount?",
            "Let's negotiate on the cost",
        ]
        for text in negotiation_texts:
            intent = IntentDetector.detect(text)
            assert intent in [Intent.NEGOTIATION, Intent.BUYING]


class TestConversationMemory:
    """Test conversation memory management"""

    def test_add_conversation_turn(self):
        memory = ConversationMemory()
        turn = memory.add_turn(
            user_id="user_1",
            user_message="Hello",
            bot_response="Hi there!",
        )
        assert turn is not None
        assert turn.user_message == "Hello"
        assert turn.bot_response == "Hi there!"

    def test_memory_preserves_history(self):
        memory = ConversationMemory()
        memory.add_turn("user_1", "First message", "First response")
        memory.add_turn("user_1", "Second message", "Second response")

        history = memory.get_history("user_1")
        assert len(history) == 2
        assert history[0].user_message == "First message"
        assert history[1].user_message == "Second message"

    def test_memory_max_history_limit(self):
        memory = ConversationMemory(max_history=3)
        for i in range(5):
            memory.add_turn("user_1", f"Message {i}", f"Response {i}")

        history = memory.get_history("user_1")
        assert len(history) == 3
        # Should keep most recent
        assert "Message 4" in history[-1].user_message

    def test_get_history_limit(self):
        memory = ConversationMemory()
        for i in range(5):
            memory.add_turn("user_1", f"Message {i}", f"Response {i}")

        recent = memory.get_history("user_1", limit=2)
        assert len(recent) == 2

    def test_separate_user_histories(self):
        memory = ConversationMemory()
        memory.add_turn("user_1", "User 1 message", "Response")
        memory.add_turn("user_2", "User 2 message", "Response")

        hist1 = memory.get_history("user_1")
        hist2 = memory.get_history("user_2")

        assert len(hist1) == 1
        assert len(hist2) == 1
        assert hist1[0].user_message == "User 1 message"
        assert hist2[0].user_message == "User 2 message"

    def test_sentiment_tracking(self):
        memory = ConversationMemory()
        memory.add_turn("user_1", "I love this!", "Great!")
        memory.add_turn("user_1", "I hate this.", "Oh no!")

        profile = memory.get_user_profile("user_1")
        sentiments = profile.preferences.get("sentiments", {})
        assert len(sentiments) > 0

    def test_intent_tracking(self):
        memory = ConversationMemory()
        memory.add_turn("user_1", "I want to buy this", "Let's proceed")
        memory.add_turn("user_1", "What features?", "Here are features")

        profile = memory.get_user_profile("user_1")
        intents = profile.preferences.get("intents", {})
        assert len(intents) > 0

    def test_context_summary(self):
        memory = ConversationMemory()
        memory.add_turn("user_1", "I want to buy a laptop", "What specs?")
        memory.add_turn("user_1", "16GB RAM, 500GB storage", "That's available")

        summary = memory.get_context_summary("user_1")
        assert "last_intent" in summary
        assert "last_sentiment" in summary
        assert "topics" in summary
        assert "recent_exchanges" in summary

    def test_user_profile_creation_and_update(self):
        memory = ConversationMemory()
        profile = memory.get_user_profile("user_1")
        assert profile.user_id == "user_1"

        updated = memory.update_profile("user_1", name="John", email="john@example.com")
        assert updated.name == "John"
        assert updated.email == "john@example.com"


class TestContextRetriever:
    """Test context retrieval for response generation"""

    def test_context_retrieval(self):
        memory = ConversationMemory()
        retriever = ContextRetriever(memory)

        memory.add_turn("user_1", "I want to buy", "Let's help")
        memory.add_turn("user_1", "What's the price?", "It's $50")

        context = retriever.get_context("user_1", "Can I get a discount?")

        assert "user_profile" in context
        assert "current_message" in context
        assert "conversation_history" in context
        assert "response_guidance" in context

    def test_context_user_profile_info(self):
        memory = ConversationMemory()
        retriever = ContextRetriever(memory)

        memory.add_turn("user_1", "Hello", "Hi!")
        context = retriever.get_context("user_1", "How are you?")

        profile = context["user_profile"]
        assert "name" in profile
        assert "conversation_count" in profile

    def test_context_current_message_info(self):
        memory = ConversationMemory()
        retriever = ContextRetriever(memory)

        memory.add_turn("user_1", "I want to buy", "Sure!")

        context = retriever.get_context("user_1", "I hate this product!")

        current = context["current_message"]
        assert "intent" in current
        assert "sentiment" in current
        assert current["sentiment"] == Sentiment.NEGATIVE.value

    def test_context_conversation_history(self):
        memory = ConversationMemory()
        retriever = ContextRetriever(memory)

        memory.add_turn("user_1", "First", "Response 1")
        memory.add_turn("user_1", "Second", "Response 2")

        context = retriever.get_context("user_1", "Third")

        history = context["conversation_history"]
        assert len(history) == 2

    def test_response_guidance_for_complaint(self):
        memory = ConversationMemory()
        retriever = ContextRetriever(memory)

        context = retriever.get_context(
            "user_1",
            "I'm very disappointed, I want a refund!"
        )

        guidance = context["response_guidance"]
        assert guidance["offer_help"] is True
        assert guidance["tone"] == "empathetic"

    def test_response_guidance_for_buying(self):
        memory = ConversationMemory()
        retriever = ContextRetriever(memory)

        context = retriever.get_context(
            "user_1",
            "I want to buy this now!"
        )

        guidance = context["response_guidance"]
        assert guidance["suggest_action"] is True
        assert guidance["urgency"] is True

    def test_response_guidance_for_new_user(self):
        memory = ConversationMemory()
        retriever = ContextRetriever(memory)

        context = retriever.get_context("new_user", "Hello!")

        guidance = context["response_guidance"]
        # New users should be more formal
        assert guidance["formality"] > 0.5

    def test_response_guidance_for_regular_user(self):
        memory = ConversationMemory()
        retriever = ContextRetriever(memory)

        # Simulate 15 conversations
        for i in range(15):
            memory.add_turn("regular_user", f"Message {i}", f"Response {i}")

        context = retriever.get_context("regular_user", "Hey!")

        guidance = context["response_guidance"]
        # Regular users should be less formal (more casual)
        assert guidance["formality"] < 0.5


class TestConversationTurn:
    """Test conversation turn structure"""

    def test_turn_creation(self):
        turn = ConversationTurn(
            timestamp=datetime.utcnow(),
            user_message="Hello",
            bot_response="Hi!",
            user_sentiment=Sentiment.POSITIVE,
            detected_intent=Intent.BUYING
        )
        assert turn.user_message == "Hello"
        assert turn.user_sentiment == Sentiment.POSITIVE
        assert turn.detected_intent == Intent.BUYING

    def test_turn_with_metadata(self):
        metadata = {"channel": "whatsapp", "session_id": "sess_123"}
        turn = ConversationTurn(
            timestamp=datetime.utcnow(),
            user_message="Test",
            bot_response="Response",
            user_sentiment=Sentiment.NEUTRAL,
            detected_intent=Intent.INFORMATION,
            metadata=metadata
        )
        assert turn.metadata["channel"] == "whatsapp"


class TestIntegration:
    """Integration tests for context recall"""

    def test_full_context_pipeline(self):
        """Test complete context recall pipeline"""
        memory = ConversationMemory()
        retriever = ContextRetriever(memory)

        # Simulate customer journey
        messages = [
            ("I'm interested in your product", Intent.BUYING),
            ("What features does it have?", Intent.INFORMATION),
            ("Price looks good, I want to buy!", Intent.BUYING),
        ]

        for user_msg, expected_intent in messages:
            memory.add_turn("customer_1", user_msg, "Response")

        # Get full context
        context = retriever.get_context("customer_1", "Can I get support?")

        # Verify context
        assert context["user_profile"]["conversation_count"] == 3
        assert len(context["conversation_history"]) == 3
        assert context["current_message"]["intent"] == Intent.SUPPORT.value

    def test_sentiment_progression(self):
        """Test tracking sentiment over time"""
        memory = ConversationMemory()

        # Simulate sentiment progression: negative -> neutral -> positive
        memory.add_turn("user_1", "This is broken!", "Let's fix it")
        memory.add_turn("user_1", "Ok, let me try", "Let me know")
        memory.add_turn("user_1", "It works great now!", "Awesome!")

        profile = memory.get_user_profile("user_1")
        sentiments = profile.preferences.get("sentiments", {})

        # Should have tracked multiple sentiments
        assert len(sentiments) > 0

    def test_multi_user_isolation(self):
        """Test that different users don't interfere"""
        memory = ConversationMemory()

        memory.add_turn("user_1", "I want to buy", "Sure!")
        memory.add_turn("user_2", "I want to sell", "Ok!")
        memory.add_turn("user_1", "What's the price?", "It's $100")

        hist1 = memory.get_history("user_1")
        hist2 = memory.get_history("user_2")

        assert len(hist1) == 2
        assert len(hist2) == 1

    def test_context_with_empty_history(self):
        """Test context retrieval for new user"""
        memory = ConversationMemory()
        retriever = ContextRetriever(memory)

        context = retriever.get_context("new_user", "Hello!")

        # Should handle new user gracefully
        assert "user_profile" in context
        assert context["user_profile"]["conversation_count"] == 0

    def test_singleton_instances(self):
        """Test singleton instances"""
        mem1 = get_conversation_memory()
        mem2 = get_conversation_memory()
        assert mem1 is mem2

        ret1 = get_context_retriever()
        ret2 = get_context_retriever()
        assert ret1 is ret2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
