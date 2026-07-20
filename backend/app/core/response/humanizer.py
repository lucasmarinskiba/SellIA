"""
Stage 1: Humanizer - Make AI responses sound authentically human

Features:
- Tone analysis (formal/casual/friendly)
- Personality injection (per user profile)
- Contextual emoji selection
- Sentence variation (avoid repetition)
- Filler word injection (uh, hmm, like, etc.)
- Intentional typo injection (2% rate)
"""

import random
from typing import Optional, List, Dict, Any
from enum import Enum
from dataclasses import dataclass
import re


class Tone(str, Enum):
    """Communication tone"""
    FORMAL = "formal"
    CASUAL = "casual"
    FRIENDLY = "friendly"
    PROFESSIONAL = "professional"
    ENTHUSIASTIC = "enthusiastic"


@dataclass
class PersonalityProfile:
    """User personality profile"""
    user_id: str
    name: str
    tone: Tone = Tone.CASUAL
    uses_emojis: bool = True
    formality_level: float = 0.5  # 0=casual, 1=formal
    humor_level: float = 0.5  # 0=serious, 1=very humorous
    language_style: str = "conversational"  # conversational, technical, poetic
    custom_traits: Dict[str, Any] = None


class ToneAnalyzer:
    """Analyze and match tone"""

    @staticmethod
    def analyze_message(content: str) -> Tone:
        """Detect tone from message content"""
        content_lower = content.lower()

        # Formal indicators
        formal_keywords = ["hereby", "furthermore", "therefore", "moreover",
                          "consequently", "thus", "accordingly"]
        if any(kw in content_lower for kw in formal_keywords):
            return Tone.FORMAL

        # Enthusiastic indicators
        enthusiastic_patterns = [r'!!!', r'\?\?', r'wow|amazing|incredible',
                                 r'love|awesome|fantastic']
        if any(re.search(p, content_lower) for p in enthusiastic_patterns):
            return Tone.ENTHUSIASTIC

        # Default to casual
        return Tone.CASUAL

    @staticmethod
    def adjust_tone(text: str, target_tone: Tone) -> str:
        """Adjust text to match tone"""
        if target_tone == Tone.FORMAL:
            # Remove contractions
            text = text.replace("don't", "do not")
            text = text.replace("can't", "cannot")
            text = text.replace("won't", "will not")
            text = text.replace("it's", "it is")
            # Remove casual phrases
            text = re.sub(r'\blike\b|\byou know\b|\bnah\b|\byup\b', '', text)
            return text.strip()

        elif target_tone == Tone.CASUAL:
            # Add contractions where natural
            text = re.sub(r'\bdo not\b', "don't", text)
            text = re.sub(r'\bcannot\b', "can't", text)
            return text

        elif target_tone == Tone.ENTHUSIASTIC:
            # Add enthusiasm
            if not text.endswith('!'):
                text = text.rstrip('.?') + '!'
            return text

        return text


class EmojiSelector:
    """Context-aware emoji selection"""

    SENTIMENT_EMOJIS = {
        "positive": ["😊", "🎉", "✨", "💪", "👏", "🔥", "💯"],
        "negative": ["😞", "😕", "😤", "⚠️", "🚫"],
        "question": ["🤔", "❓", "🤷"],
        "love": ["❤️", "💕", "😍"],
        "money": ["💰", "💵", "📈", "💸"],
        "growth": ["📈", "🚀", "⬆️", "🌱"],
        "success": ["🏆", "✅", "🎯", "👌"],
        "action": ["⚡", "💨", "🏃", "⏰"],
    }

    @staticmethod
    def select_emoji(text: str, sentiment: str = "positive") -> str:
        """Select contextual emoji based on content"""
        keywords_map = {
            "money": ["price", "cost", "payment", "affordable", "expensive",
                     "budget", "invest"],
            "growth": ["grow", "increase", "scale", "expand", "boost",
                      "improve", "rise"],
            "success": ["success", "achieve", "win", "accomplish", "complete",
                       "done", "finished", "perfect"],
            "action": ["now", "hurry", "urgent", "quick", "fast", "asap"],
            "question": ["why", "how", "what", "when", "where"],
        }

        text_lower = text.lower()
        for keyword_type, keywords in keywords_map.items():
            if any(kw in text_lower for kw in keywords):
                return random.choice(EmojiSelector.SENTIMENT_EMOJIS.get(
                    keyword_type, EmojiSelector.SENTIMENT_EMOJIS["positive"]))

        return random.choice(EmojiSelector.SENTIMENT_EMOJIS.get(sentiment, []))


class SentenceVariator:
    """Avoid repetition through sentence variation"""

    SENTENCE_STARTERS = [
        "I think", "From what I understand", "Based on this",
        "It seems", "You know", "I'd say", "Check this out",
        "Here's the thing", "Consider this", "Think about it"
    ]

    AGREEMENT_PHRASES = [
        "Absolutely", "For sure", "Yeah", "Totally", "Definitely",
        "No doubt", "You're right", "Exactly", "Spot on", "No cap"
    ]

    TRANSITION_WORDS = [
        "Plus", "Also", "Moreover", "Additionally", "On top of that",
        "By the way", "Speaking of which", "That said", "Anyway", "So"
    ]

    @staticmethod
    def add_variety(text: str, variation_level: float = 0.5) -> str:
        """Add sentence variation"""
        sentences = text.split('. ')
        varied = []

        for i, sentence in enumerate(sentences):
            if random.random() < variation_level and i > 0:
                # Add transition word
                transition = random.choice(SentenceVariator.TRANSITION_WORDS)
                sentence = f"{transition}, {sentence[0].lower()}{sentence[1:]}"

            varied.append(sentence)

        return '. '.join(varied)

    @staticmethod
    def vary_response(text: str, personality: Optional[PersonalityProfile] = None) -> str:
        """Apply variation based on personality"""
        if not personality or personality.language_style != "conversational":
            return text

        return SentenceVariator.add_variety(text, variation_level=0.6)


class FillerWordInjector:
    """Add natural filler words"""

    FILLER_WORDS = {
        "light": ["uh", "um", "you know", "like"],
        "medium": ["actually", "honestly", "basically", "kinda", "sorta"],
        "heavy": ["literally", "obviously", "I mean", "for real", "no cap"]
    }

    @staticmethod
    def inject_fillers(text: str, intensity: str = "light") -> str:
        """Add filler words naturally"""
        if intensity not in FillerWordInjector.FILLER_WORDS:
            intensity = "light"

        sentences = text.split('. ')
        result = []

        for sentence in sentences:
            if len(sentence) > 20 and random.random() < 0.3:  # 30% of sentences
                filler = random.choice(FillerWordInjector.FILLER_WORDS[intensity])
                # Insert after first word or at beginning
                words = sentence.split(' ', 1)
                if len(words) > 1:
                    sentence = f"{words[0]} {filler}, {words[1]}"
                else:
                    sentence = f"{filler}, {sentence}"

            result.append(sentence)

        return '. '.join(result)


class TypoInjector:
    """Intentional typo injection for authenticity (2% rate)"""

    COMMON_TYPOS = {
        "the": ["teh", "th"],
        "that": ["taht", "that"],
        "and": ["adn", "abd"],
        "because": ["becuase", "b/c"],
        "people": ["ppl", "peopl"],
        "your": ["ur", "youre"],
        "you": ["u", "yo"],
    }

    @staticmethod
    def introduce_typos(text: str, typo_rate: float = 0.02) -> str:
        """Introduce intentional typos for authenticity"""
        words = text.split()
        result = []

        for word in words:
            # Only introduce typos in common words
            word_lower = word.lower().strip('.,!?')
            if word_lower in TypoInjector.COMMON_TYPOS and random.random() < typo_rate:
                typo = random.choice(TypoInjector.COMMON_TYPOS[word_lower])
                # Preserve case and punctuation
                punctuation = ''.join(c for c in word if c in '.,!?')
                if word[0].isupper():
                    typo = typo.capitalize()
                result.append(typo + punctuation)
            else:
                result.append(word)

        return ' '.join(result)


class Humanizer:
    """Main humanizer orchestrator"""

    def __init__(self):
        self.tone_analyzer = ToneAnalyzer()
        self.emoji_selector = EmojiSelector()
        self.sentence_variator = SentenceVariator()
        self.filler_injector = FillerWordInjector()
        self.typo_injector = TypoInjector()

    def humanize(
        self,
        text: str,
        personality: Optional[PersonalityProfile] = None,
        use_emojis: bool = True,
        add_typos: bool = True,
        filler_intensity: str = "light"
    ) -> str:
        """
        Full humanization pipeline:
        1. Tone adjustment
        2. Sentence variation
        3. Filler word injection
        4. Typo injection
        5. Emoji addition
        """
        # Use personality or default
        if personality is None:
            personality = PersonalityProfile(
                user_id="default",
                name="Assistant",
                tone=self.tone_analyzer.analyze_message(text)
            )

        # Step 1: Adjust tone
        text = self.tone_analyzer.adjust_tone(text, personality.tone)

        # Step 2: Add sentence variety
        text = self.sentence_variator.vary_response(text, personality)

        # Step 3: Inject filler words
        text = self.filler_injector.inject_fillers(text, filler_intensity)

        # Step 4: Add typos (optional)
        if add_typos and random.random() < 0.5:  # 50% of responses
            text = self.typo_injector.introduce_typos(text, typo_rate=0.02)

        # Step 5: Add emojis (optional)
        if use_emojis and personality.uses_emojis:
            emoji = self.emoji_selector.select_emoji(text)
            # Add emoji at end or in middle naturally
            if random.random() < 0.6:
                text = f"{text} {emoji}"

        return text

    def humanize_for_user(
        self,
        text: str,
        user_profile: PersonalityProfile
    ) -> str:
        """Humanize based on specific user profile"""
        filler_intensity = {
            0.2: "heavy",
            0.5: "medium",
            0.8: "light"
        }[min(filler_intensity.keys(),
              key=lambda x: abs(x - user_profile.formality_level))]

        return self.humanize(
            text,
            personality=user_profile,
            use_emojis=user_profile.uses_emojis,
            add_typos=not user_profile.language_style == "technical",
            filler_intensity=filler_intensity
        )

    def quality_score(self, original: str, humanized: str) -> Dict[str, Any]:
        """Score humanization quality"""
        scores = {
            "tone_varied": len(set(humanized.split())) > len(set(original.split())),
            "has_emoji": "😊" in humanized or "🎉" in humanized or any(
                ord(c) > 127 for c in humanized
            ),
            "has_variation": original != humanized,
            "length_reasonable": 0.8 <= len(humanized) / max(len(original), 1) <= 1.2,
            "readability": len(humanized) < 500  # Not too long
        }

        score = sum(scores.values()) / len(scores)
        return {
            "overall_score": score,
            "components": scores
        }


# Singleton
_humanizer_instance: Optional[Humanizer] = None


def get_humanizer() -> Humanizer:
    """Get or create humanizer singleton"""
    global _humanizer_instance
    if _humanizer_instance is None:
        _humanizer_instance = Humanizer()
    return _humanizer_instance
