"""
Humor Generator — Context-aware jokes, timing, authenticity.

Generates:
1. Punny jokes (wordplay)
2. Witty observations
3. Relatable humor
4. Self-deprecating humor
5. Product-specific jokes
6. Timing-appropriate humor
7. Emoji integration
"""

import logging
from typing import Dict, List, Any, Tuple
from enum import Enum
from random import choice, randint

logger = logging.getLogger(__name__)


class HumorStyle(str, Enum):
    """Humor style types."""
    PUNNY = "punny"  # Wordplay
    WITTY = "witty"  # Clever observation
    RELATABLE = "relatable"  # Common experience
    SELF_DEPRECATING = "self_deprecating"  # Self-aware humor
    DARK = "dark"  # Edgy humor (use carefully)


class HumorTone(str, Enum):
    """Humor tone/intensity."""
    LIGHT = "light"  # Gentle, safe
    PLAYFUL = "playful"  # Fun, engaging
    SARCASTIC = "sarcastic"  # Sharp, clever
    WITTY_SHARP = "witty_sharp"  # Cutting edge


class HumorGenerator:
    """Generates context-aware humor."""

    # Pun templates (product/industry agnostic)
    PUN_TEMPLATES = [
        "Honestly, this comment deserves {adjective} applause",
        "You could say this is {adjective}... core",
        "That's a pretty {adjective} take on things",
        "No pun intended, but you've really {verb}ed my day",
        "{Adjective}? More like {funny_twist}!",
        "I see what you did there, and it's absolutely {adjective}",
    ]

    # Witty observations
    WITTY_TEMPLATES = [
        "You know what they say: {observation}",
        "Fun fact: {observation}",
        "Takes one to know one: {observation}",
        "{observation} — and I'm here for it",
    ]

    # Relatable humor patterns
    RELATABLE_PATTERNS = {
        "coffee": [
            "Spoken like someone who hasn't had enough coffee yet",
            "This hits different before the first coffee",
            "Coffee-first thought right here",
        ],
        "monday": [
            "Is it Monday or is that just the energy?",
            "Monday vibe right there",
            "Monday called, wants its energy back",
        ],
        "night_work": [
            "This has 2am energy written all over it",
            "Late-night thoughts are the best thoughts",
            "Someone was definitely coding past midnight",
        ],
    }

    # Self-deprecating templates
    SELF_DEPRECATING_TEMPLATES = [
        "I mean... we're not perfect, but this is a good reminder why",
        "Bold of you to assume we haven't thought of this",
        "Us actually delivering that? {outcome}",
        "We tried... emphasis on tried",
    ]

    # Dad jokes (safe for all audiences)
    DAD_JOKES = [
        "Why did the {thing} go to {place}? To have a {outcome}!",
        "You could say this comment is pretty... {adjective} {thing}",
        "I {action}, therefore I {result}",
    ]

    # Reaction emojis (context-aware)
    REACTION_EMOJIS = {
        "approval": ["👏", "🙌", "✨", "🔥"],
        "laugh": ["😂", "🤣", "😆"],
        "thinking": ["🤔", "💭", "🧠"],
        "surprise": ["😲", "😮", "🤯"],
        "love": ["❤️", "💕", "😍"],
        "celebration": ["🎉", "🎊", "🥳"],
    }

    @staticmethod
    def generate_punny_response(topic: str, subject: str) -> Dict[str, Any]:
        """
        Generate pun-based response.

        Args:
            topic: What the pun is about
            subject: What to make a pun about

        Returns:
            {
                "pun": str,
                "style": "punny",
                "strength": 0-100,
                "explanation": str,
            }
        """

        # Common pun mappings
        pun_map = {
            "code": ["code-ial", "code-d", "debug-utiful"],
            "feature": ["feature-ing", "feat-ured", "feature-full"],
            "api": ["app-solutely", "a-peel", "app-reciate"],
            "deploy": ["de-ploy-ed", "deploy-ment", "deploy-joy"],
            "bug": ["bug-tastic", "bug-ger off", "bug-me"],
            "performance": ["perf-ection", "perf-orm", "perf-ormance"],
        }

        # Get pun variations for topic
        puns_for_topic = pun_map.get(topic.lower(), [])

        if puns_for_topic:
            pun = choice(puns_for_topic)
            response = f"Looks like {subject} has earned the '{pun}' badge!"
            strength = 75
        else:
            # Generic pun
            response = f"That {subject} is absolutely punny!"
            strength = 50

        return {
            "pun": response,
            "style": HumorStyle.PUNNY.value,
            "strength": strength,
            "explanation": "Wordplay-based humor",
            "safe_for_all": True,
        }

    @staticmethod
    def generate_witty_response(context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate witty observation-based response.

        Returns:
            {
                "response": str,
                "style": "witty",
                "strength": 0-100,
            }
        """

        observations = [
            "You've clearly put thought into this",
            "This is the kind of question that keeps me up at night",
            "You're asking the real questions here",
            "Someone's thinking strategically",
            "This comment deserves more engagement",
            "Plot twist: You understand our product better than expected",
        ]

        response = choice(observations)
        strength = randint(70, 90)

        return {
            "response": response,
            "style": HumorStyle.WITTY.value,
            "strength": strength,
            "explanation": "Clever observation",
            "safe_for_all": True,
        }

    @staticmethod
    def generate_relatable_response(context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate relatable humor based on common experiences.

        Returns:
            {
                "response": str,
                "style": "relatable",
                "strength": 0-100,
                "trigger": str,
            }
        """

        # Detect relatable trigger
        timestamp = context.get("timestamp", "")
        comment_text = context.get("text", "").lower()

        trigger = None
        response_options = []

        if any(word in comment_text for word in ["coffee", "caffeine", "tired"]):
            trigger = "coffee"
            response_options = HumorGenerator.RELATABLE_PATTERNS["coffee"]
        elif any(word in comment_text for word in ["monday", "start", "week"]):
            trigger = "monday"
            response_options = HumorGenerator.RELATABLE_PATTERNS["monday"]
        elif any(word in comment_text for word in ["late", "night", "3am", "sleep"]):
            trigger = "night_work"
            response_options = HumorGenerator.RELATABLE_PATTERNS["night_work"]

        if response_options:
            response = choice(response_options)
            strength = 85
        else:
            response = "This is so relatable it hurts"
            strength = 70
            trigger = "general_relatable"

        return {
            "response": response,
            "style": HumorStyle.RELATABLE.value,
            "strength": strength,
            "trigger": trigger,
            "explanation": "Relatable common experience",
            "safe_for_all": True,
        }

    @staticmethod
    def generate_self_deprecating_response(
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate self-aware, humble humor.

        Returns:
            {
                "response": str,
                "style": "self_deprecating",
                "strength": 0-100,
            }
        """

        templates = [
            "Wow, called out! You're not wrong though",
            "This is the kind of feedback that keeps us humble",
            "You just articulated what our CEO thinks at 3am",
            "Guilty as charged. We're working on it 😅",
            "Yeah... we know. It's on the roadmap... somewhere",
            "Bold of you to assume we've thought about this",
        ]

        response = choice(templates)

        return {
            "response": response,
            "style": HumorStyle.SELF_DEPRECATING.value,
            "strength": 80,
            "explanation": "Self-aware, humble humor",
            "safe_for_all": True,
        }

    @staticmethod
    def check_timing_appropriateness(
        comment_sentiment: str,
        comment_intent: str,
        audience_type: str,
    ) -> Dict[str, Any]:
        """
        Check if humor is appropriate for this comment.

        Returns:
            {
                "humor_appropriate": bool,
                "intensity": "light" | "playful" | "sarcastic",
                "styles_to_avoid": [list],
                "reasoning": str,
            }
        """

        humor_appropriate = True
        intensity = HumorTone.PLAYFUL
        styles_to_avoid = []
        reasoning = ""

        # If very negative sentiment, be careful
        if comment_sentiment in ["very_negative", "negative"]:
            if comment_intent == "criticism":
                # Can use self-deprecating humor
                styles_to_avoid = [HumorStyle.SARCASTIC, HumorStyle.DARK]
                intensity = HumorTone.LIGHT
                reasoning = "Negative comment → lighter, self-aware humor only"

        # If praise, can be more playful
        elif comment_sentiment in ["very_positive", "positive"]:
            intensity = HumorTone.PLAYFUL
            reasoning = "Positive comment → playful humor works great"

        # If audience is decision-maker, be careful
        if audience_type == "decision_maker":
            if comment_intent in ["question", "concern"]:
                humor_appropriate = False
                reasoning = "Decision-maker's serious question → humor may backfire"
            else:
                intensity = HumorTone.LIGHT
                styles_to_avoid = [HumorStyle.SARCASTIC, HumorStyle.DARK]
                reasoning = "Decision-maker → light humor only, avoid sarcasm"

        # If troll, avoid humor (don't feed)
        if audience_type == "troll":
            humor_appropriate = False
            reasoning = "Troll comment → humor encourages engagement, respond professionally"

        return {
            "humor_appropriate": humor_appropriate,
            "intensity": intensity.value,
            "styles_to_avoid": [s.value for s in styles_to_avoid],
            "reasoning": reasoning,
            "confidence": 85,
        }

    @staticmethod
    def integrate_emoji(
        response_text: str,
        emoji_strategy: str = "enhance",
    ) -> Dict[str, Any]:
        """
        Integrate emojis to enhance response.

        Strategies:
        - enhance: Add 1-2 relevant emojis
        - subtle: Add emoji only at end
        - heavy: Add multiple emojis (fun tone)

        Returns:
            {
                "response_with_emoji": str,
                "emojis_added": [list],
                "strategy": str,
            }
        """

        emojis_added = []

        # Detect emotion/tone from text
        if any(word in response_text.lower() for word in ["love", "awesome", "great", "thank"]):
            emojis_to_add = HumorGenerator.REACTION_EMOJIS["love"]
        elif any(word in response_text.lower() for word in ["laugh", "funny", "ha"]):
            emojis_to_add = HumorGenerator.REACTION_EMOJIS["laugh"]
        elif any(word in response_text.lower() for word in ["wow", "amazing", "impressive"]):
            emojis_to_add = HumorGenerator.REACTION_EMOJIS["celebration"]
        elif any(word in response_text.lower() for word in ["think", "consider", "interesting"]):
            emojis_to_add = HumorGenerator.REACTION_EMOJIS["thinking"]
        else:
            emojis_to_add = HumorGenerator.REACTION_EMOJIS["approval"]

        if emoji_strategy == "enhance":
            emoji = choice(emojis_to_add)
            emoji_response = f"{response_text} {emoji}"
            emojis_added = [emoji]
        elif emoji_strategy == "subtle":
            emoji = choice(emojis_to_add)
            emoji_response = f"{response_text} {emoji}"
            emojis_added = [emoji]
        elif emoji_strategy == "heavy":
            selected_emojis = emojis_to_add[:2] if len(emojis_to_add) > 1 else emojis_to_add
            emoji_response = f"{response_text} {' '.join(selected_emojis)}"
            emojis_added = selected_emojis
        else:
            emoji_response = response_text

        return {
            "response_with_emoji": emoji_response,
            "emojis_added": emojis_added,
            "strategy": emoji_strategy,
        }

    @staticmethod
    def generate_humor_response(
        comment_sentiment: str,
        comment_intent: str,
        comment_text: str,
        audience_type: str,
        preferred_style: str = None,
    ) -> Dict[str, Any]:
        """
        Generate complete humor-based response.

        Returns:
            {
                "response": str,
                "style": str,
                "strength": 0-100,
                "reasoning": str,
                "recommendation": str,
            }
        """

        # Check timing appropriateness
        timing = HumorGenerator.check_timing_appropriateness(
            comment_sentiment, comment_intent, audience_type
        )

        if not timing["humor_appropriate"]:
            return {
                "response": None,
                "style": "not_appropriate",
                "strength": 0,
                "reasoning": timing["reasoning"],
                "recommendation": "Use professional tone instead",
            }

        # Select humor style based on context
        if preferred_style and preferred_style not in timing["styles_to_avoid"]:
            style_choice = preferred_style
        else:
            # Default selection based on sentiment/intent
            if comment_sentiment in ["very_negative", "negative"]:
                style_choice = HumorStyle.SELF_DEPRECATING
            elif comment_intent == "praise":
                style_choice = HumorStyle.WITTY
            elif comment_intent == "question":
                style_choice = HumorStyle.RELATABLE
            else:
                style_choice = HumorStyle.PUNNY

        # Generate response based on style
        if style_choice == HumorStyle.PUNNY:
            result = HumorGenerator.generate_punny_response("general", "comment")
        elif style_choice == HumorStyle.WITTY:
            result = HumorGenerator.generate_witty_response({"text": comment_text})
        elif style_choice == HumorStyle.RELATABLE:
            result = HumorGenerator.generate_relatable_response({"text": comment_text})
        elif style_choice == HumorStyle.SELF_DEPRECATING:
            result = HumorGenerator.generate_self_deprecating_response({})
        else:
            result = HumorGenerator.generate_witty_response({"text": comment_text})

        # Add emoji if appropriate
        emoji_result = HumorGenerator.integrate_emoji(
            result["pun"] if "pun" in result else result.get("response", ""),
            emoji_strategy="enhance" if timing["intensity"] == HumorTone.PLAYFUL.value else "subtle",
        )

        return {
            "response": emoji_result["response_with_emoji"],
            "style": result.get("style"),
            "strength": result.get("strength", 70),
            "intensity": timing["intensity"],
            "reasoning": result.get("explanation", ""),
            "recommendation": "Use this humor approach",
            "emojis_used": emoji_result["emojis_added"],
        }
