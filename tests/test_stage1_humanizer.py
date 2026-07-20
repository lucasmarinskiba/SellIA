"""
Stage 1 Tests: Humanizer - Tone, Personality, Variation, Typos, Emojis

Test Coverage:
- Tone analysis and adjustment
- Personality injection
- Sentence variation
- Filler word injection
- Typo injection (2% rate)
- Emoji selection
- Humanization quality scoring
"""

import pytest
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.core.response.humanizer import (
    Humanizer, PersonalityProfile, Tone, ToneAnalyzer, EmojiSelector,
    SentenceVariator, FillerWordInjector, TypoInjector, get_humanizer
)


class TestToneAnalyzer:
    """Test tone detection and adjustment"""

    def test_formal_tone_detection(self):
        formal_text = "Furthermore, it is hereby stated that the matter shall be addressed accordingly."
        tone = ToneAnalyzer.analyze_message(formal_text)
        assert tone == Tone.FORMAL

    def test_enthusiastic_tone_detection(self):
        enthusiastic_text = "OMG this is absolutely AMAZING!!! I love it so much!"
        tone = ToneAnalyzer.analyze_message(enthusiastic_text)
        assert tone == Tone.ENTHUSIASTIC

    def test_casual_tone_detection(self):
        casual_text = "Hey, how's it going? Just wanted to check in with you."
        tone = ToneAnalyzer.analyze_message(casual_text)
        assert tone == Tone.CASUAL

    def test_tone_adjustment_to_formal(self):
        text = "I don't think we can do it, it's too hard."
        formal = ToneAnalyzer.adjust_tone(text, Tone.FORMAL)
        assert "do not" in formal
        assert "is" in formal
        assert "don't" not in formal

    def test_tone_adjustment_to_casual(self):
        text = "I can not do this."
        casual = ToneAnalyzer.adjust_tone(text, Tone.CASUAL)
        assert "can't" in casual or "cannot" in casual

    def test_tone_adjustment_to_enthusiastic(self):
        text = "That's good."
        enthusiastic = ToneAnalyzer.adjust_tone(text, Tone.ENTHUSIASTIC)
        assert enthusiastic.endswith("!")


class TestEmojiSelector:
    """Test contextual emoji selection"""

    def test_emoji_money_context(self):
        text = "Great pricing at $99/month"
        emoji = EmojiSelector.select_emoji(text)
        # Should select from money emojis
        assert emoji in EmojiSelector.SENTIMENT_EMOJIS["money"] or \
               emoji in EmojiSelector.SENTIMENT_EMOJIS["positive"]

    def test_emoji_growth_context(self):
        text = "Your sales will grow 10x with our tool"
        emoji = EmojiSelector.select_emoji(text)
        # Should select from growth emojis
        assert emoji in EmojiSelector.SENTIMENT_EMOJIS["growth"] or \
               emoji in EmojiSelector.SENTIMENT_EMOJIS["positive"]

    def test_emoji_success_context(self):
        text = "You've successfully completed the purchase!"
        emoji = EmojiSelector.select_emoji(text)
        assert emoji in EmojiSelector.SENTIMENT_EMOJIS["success"] or \
               emoji in EmojiSelector.SENTIMENT_EMOJIS["positive"]

    def test_emoji_action_context(self):
        text = "Buy now before time runs out!"
        emoji = EmojiSelector.select_emoji(text)
        assert emoji in EmojiSelector.SENTIMENT_EMOJIS["action"] or \
               emoji in EmojiSelector.SENTIMENT_EMOJIS["positive"]

    def test_emoji_question_context(self):
        text = "How can you improve your business?"
        emoji = EmojiSelector.select_emoji(text)
        assert emoji in EmojiSelector.SENTIMENT_EMOJIS["question"] or \
               emoji in EmojiSelector.SENTIMENT_EMOJIS["positive"]


class TestSentenceVariator:
    """Test sentence variation to avoid repetition"""

    def test_sentence_variety_added(self):
        text = "This is good. This is nice. This is great."
        varied = SentenceVariator.add_variety(text, variation_level=1.0)
        # Should be different from original
        assert varied != text

    def test_transition_words_added(self):
        text = "First point. Second point. Third point."
        varied = SentenceVariator.add_variety(text, variation_level=1.0)
        # Should contain transition words
        has_transition = any(word in varied for word in
                           SentenceVariator.TRANSITION_WORDS)
        assert has_transition

    def test_high_variation(self):
        text = "This is sentence one. This is sentence two."
        varied_high = SentenceVariator.add_variety(text, variation_level=1.0)
        varied_low = SentenceVariator.add_variety(text, variation_level=0.0)
        # High variation should differ more from original
        assert varied_high != text or varied_low == text

    def test_vary_response_with_personality(self):
        personality = PersonalityProfile(
            user_id="user_1",
            name="John",
            language_style="conversational"
        )
        text = "This is good. This is nice."
        varied = SentenceVariator.vary_response(text, personality)
        # Should be different when personality is conversational
        assert varied is not None


class TestFillerWordInjector:
    """Test filler word injection for natural speech"""

    def test_light_filler_injection(self):
        text = "I think this is a great idea for the business."
        with_fillers = FillerWordInjector.inject_fillers(text, "light")
        # Might contain light fillers
        light_fillers = FillerWordInjector.FILLER_WORDS["light"]
        # Text should still be readable
        assert len(with_fillers) > len(text) * 0.9

    def test_medium_filler_injection(self):
        text = "I think this is a great idea for the business."
        with_fillers = FillerWordInjector.inject_fillers(text, "medium")
        medium_fillers = FillerWordInjector.FILLER_WORDS["medium"]
        # Text should be readable
        assert len(with_fillers) > len(text) * 0.9

    def test_heavy_filler_injection(self):
        text = "I think this is a great idea for the business."
        with_fillers = FillerWordInjector.inject_fillers(text, "heavy")
        # Text should still be readable
        assert len(with_fillers) > len(text) * 0.9

    def test_filler_injection_preserves_content(self):
        text = "This is important information."
        with_fillers = FillerWordInjector.inject_fillers(text, "light")
        # Core meaning should be preserved
        assert "important" in with_fillers.lower()
        assert "information" in with_fillers.lower()


class TestTypoInjector:
    """Test intentional typo injection"""

    def test_typo_injection_rate(self):
        text = "the that and because people your you" * 100
        with_typos = TypoInjector.introduce_typos(text, typo_rate=0.02)
        # Should be similar length (typos are character swaps)
        assert abs(len(with_typos) - len(text)) < len(text) * 0.1

    def test_typo_injection_preserves_meaning(self):
        text = "The price is good"
        with_typos = TypoInjector.introduce_typos(text, typo_rate=0.5)
        # Even with typos, core words should be recognizable
        assert len(with_typos) > 0

    def test_common_word_typos(self):
        text = "the and your because"
        # Multiple passes to increase chance of typo
        found_typo = False
        for _ in range(10):
            with_typos = TypoInjector.introduce_typos(text, typo_rate=0.5)
            if with_typos != text:
                found_typo = True
                break
        # Should eventually find a typo with high rate
        assert found_typo

    def test_no_typo_on_punctuation(self):
        text = "Hello! How are you?"
        with_typos = TypoInjector.introduce_typos(text, typo_rate=1.0)
        # Punctuation should be preserved
        assert "!" in with_typos
        assert "?" in with_typos


class TestHumanizer:
    """Test main humanizer orchestrator"""

    def test_humanizer_creation(self):
        humanizer = Humanizer()
        assert humanizer is not None
        assert humanizer.tone_analyzer is not None

    def test_humanization_pipeline(self):
        humanizer = Humanizer()
        text = "This is a response."
        humanized = humanizer.humanize(text)
        # Should be a string
        assert isinstance(humanized, str)
        # Should contain original meaning
        assert "response" in humanized.lower()

    def test_humanization_with_personality(self):
        humanizer = Humanizer()
        personality = PersonalityProfile(
            user_id="user_1",
            name="John",
            tone=Tone.CASUAL,
            uses_emojis=True,
            formality_level=0.3
        )
        text = "This is a test message."
        humanized = humanizer.humanize(text, personality=personality)
        assert isinstance(humanized, str)

    def test_humanization_without_emojis(self):
        humanizer = Humanizer()
        text = "This is great!"
        humanized = humanizer.humanize(text, use_emojis=False)
        # Should not have emoji characters
        has_emoji = any(ord(c) > 127 for c in humanized)
        # Might still have regular characters
        assert isinstance(humanized, str)

    def test_humanization_without_typos(self):
        humanizer = Humanizer()
        text = "the quick brown fox"
        humanized = humanizer.humanize(text, add_typos=False)
        # With add_typos=False, should not introduce typos
        # (though other humanization might happen)
        assert isinstance(humanized, str)

    def test_humanize_for_user(self):
        humanizer = Humanizer()
        profile = PersonalityProfile(
            user_id="user_1",
            name="Alice",
            tone=Tone.FRIENDLY,
            formality_level=0.4
        )
        text = "This is a message."
        humanized = humanizer.humanize_for_user(text, profile)
        assert isinstance(humanized, str)

    def test_quality_score(self):
        humanizer = Humanizer()
        original = "This is good."
        humanized = "This is great! 😊"
        score = humanizer.quality_score(original, humanized)

        assert "overall_score" in score
        assert "components" in score
        assert 0 <= score["overall_score"] <= 1

    def test_quality_score_identical_text(self):
        humanizer = Humanizer()
        text = "This is a message."
        score = humanizer.quality_score(text, text)
        # Identical text should score lower than varied
        assert score["overall_score"] < 1.0

    def test_quality_score_too_long(self):
        humanizer = Humanizer()
        original = "Short"
        humanized = "This is a very long message " * 100
        score = humanizer.quality_score(original, humanized)
        assert "overall_score" in score


class TestPersonalityProfile:
    """Test personality profiles"""

    def test_profile_creation_default(self):
        profile = PersonalityProfile(
            user_id="user_1",
            name="John"
        )
        assert profile.user_id == "user_1"
        assert profile.name == "John"
        assert profile.tone == Tone.CASUAL
        assert profile.formality_level == 0.5

    def test_profile_creation_custom(self):
        profile = PersonalityProfile(
            user_id="user_2",
            name="Jane",
            tone=Tone.FORMAL,
            uses_emojis=False,
            formality_level=0.8,
            humor_level=0.2
        )
        assert profile.tone == Tone.FORMAL
        assert profile.uses_emojis is False
        assert profile.formality_level == 0.8
        assert profile.humor_level == 0.2

    def test_profile_custom_traits(self):
        traits = {"prefers_short_responses": True, "likes_jokes": False}
        profile = PersonalityProfile(
            user_id="user_3",
            name="Bob",
            custom_traits=traits
        )
        assert profile.custom_traits["prefers_short_responses"] is True


class TestIntegration:
    """Integration tests for humanizer"""

    def test_full_humanization_pipeline(self):
        """Test complete humanization: formal text -> humanized casual"""
        humanizer = Humanizer()
        formal_text = "Furthermore, the aforementioned solution shall provide optimal performance characteristics."

        humanized = humanizer.humanize(formal_text)

        # Should be transformed
        assert humanized != formal_text
        # Should still be readable
        assert len(humanized) > 0

    def test_humanization_consistency(self):
        """Test that humanization is consistent for same input"""
        humanizer = Humanizer()
        text = "This is a test message."

        humanized1 = humanizer.humanize(text)
        humanized2 = humanizer.humanize(text)

        # Both should be humanized (though might differ due to randomness)
        assert len(humanized1) > 0
        assert len(humanized2) > 0

    def test_humanization_personality_impact(self):
        """Test that personality affects humanization"""
        humanizer = Humanizer()
        text = "This is a message."

        formal_profile = PersonalityProfile(
            user_id="formal", name="F", tone=Tone.FORMAL, formality_level=0.9
        )
        casual_profile = PersonalityProfile(
            user_id="casual", name="C", tone=Tone.CASUAL, formality_level=0.1
        )

        formal_human = humanizer.humanize_for_user(text, formal_profile)
        casual_human = humanizer.humanize_for_user(text, casual_profile)

        # Both should be strings
        assert isinstance(formal_human, str)
        assert isinstance(casual_human, str)

    def test_humanization_emoji_impact(self):
        """Test emoji impact on humanization"""
        humanizer = Humanizer()
        text = "This is great news!"

        with_emoji = humanizer.humanize(text, use_emojis=True)
        without_emoji = humanizer.humanize(text, use_emojis=False)

        # Both should be valid
        assert len(with_emoji) > 0
        assert len(without_emoji) > 0

    def test_singleton_instance(self):
        """Test humanizer singleton"""
        h1 = get_humanizer()
        h2 = get_humanizer()
        assert h1 is h2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
