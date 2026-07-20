"""
Authenticity Engine — Ensures personality consistency, genuine tone, real stories.

Checks:
1. Personality consistency (be the same person)
2. Tone authenticity (not corporate robot)
3. Story validation (real stories, not fiction)
4. Vulnerability permission (ok to admit limitations)
5. Growth mindset (show progress, not perfection)
"""

import logging
from typing import Dict, List, Any, Tuple
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class AuthenticityDimension(str, Enum):
    """Authenticity check dimensions."""
    PERSONALITY = "personality"  # Consistent persona
    TONE = "tone"  # Real vs corporate
    STORIES = "stories"  # True narratives
    VULNERABILITY = "vulnerability"  # Admits limitations
    GROWTH = "growth"  # Shows progress


class AuthenticityEngine:
    """Ensures authentic, human communication."""

    # Corporate/robotic phrases to avoid
    CORPORATE_PHRASES = [
        "synergize", "leverage", "optimize", "paradigm shift",
        "circle back", "move the needle", "drill down",
        "at the end of the day", "it goes without saying",
        "in this day and age", "take it to the next level",
        "achieve maximum efficiency", "disruptive innovation",
        "reach out", "touch base", "deep dive",
    ]

    # Authentic language patterns
    AUTHENTIC_PATTERNS = {
        "personal": ["I", "we", "my", "our", "personally", "honestly"],
        "specific": ["specifically", "for example", "actually", "realistically"],
        "vulnerable": ["struggle", "mistake", "challenge", "difficult", "learned"],
        "growth": ["improved", "evolved", "discovered", "realized", "growth"],
    }

    # Personality archetype definitions
    PERSONALITY_ARCHETYPES = {
        "founder": {
            "traits": ["entrepreneurial", "risk-taker", "visionary", "hardworking"],
            "phrases": ["we built", "we learned", "our journey", "we failed"],
            "voice_level": "casual",
        },
        "expert": {
            "traits": ["knowledgeable", "analytical", "evidence-based", "experienced"],
            "phrases": ["research shows", "based on data", "I've seen", "the pattern is"],
            "voice_level": "professional_approachable",
        },
        "friend": {
            "traits": ["relatable", "supportive", "genuine", "honest"],
            "phrases": ["honestly", "I get it", "same", "totally understand"],
            "voice_level": "casual_warm",
        },
        "guide": {
            "traits": ["helpful", "patient", "clear", "empathetic"],
            "phrases": ["here's what", "let me show you", "step by step"],
            "voice_level": "warm_instructive",
        },
    }

    @staticmethod
    def check_personality_consistency(
        current_message: str,
        historical_messages: List[str],
        declared_personality: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Check if current message matches established personality.

        Returns:
            {
                "consistent": bool,
                "personality_score": 0-100,
                "detected_archetype": str,
                "alignment_with_declared": float,
                "inconsistencies": [list],
            }
        """

        # Detect personality archetype in current message
        archetype_scores = {}
        for archetype, archetype_data in AuthenticityEngine.PERSONALITY_ARCHETYPES.items():
            traits = archetype_data["traits"]
            phrases = archetype_data["phrases"]

            trait_match = sum(
                1 for trait in traits if trait.lower() in current_message.lower()
            )
            phrase_match = sum(
                1 for phrase in phrases if phrase.lower() in current_message.lower()
            )

            archetype_scores[archetype] = (trait_match * 10) + (phrase_match * 15)

        detected_archetype = max(archetype_scores, key=archetype_scores.get)
        declared_archetype = declared_personality.get("archetype", "unknown")

        # Check consistency
        alignment = 0
        if detected_archetype == declared_archetype:
            alignment = 100
        elif detected_archetype in declared_personality.get("secondary_archetypes", []):
            alignment = 70
        else:
            alignment = 30

        # Analyze messages for consistent patterns
        inconsistencies = []

        # Check tone consistency
        tone_profile_current = AuthenticityEngine._analyze_tone(current_message)
        if historical_messages:
            tone_profile_historical = AuthenticityEngine._analyze_tone(" ".join(historical_messages))
            tone_differences = abs(tone_profile_current["formality"] - tone_profile_historical["formality"])
            if tone_differences > 30:
                inconsistencies.append({
                    "type": "tone_shift",
                    "previous_formality": tone_profile_historical["formality"],
                    "current_formality": tone_profile_current["formality"],
                    "severity": "medium",
                })

        # Check vocabulary consistency
        corporate_count_current = sum(
            1 for phrase in AuthenticityEngine.CORPORATE_PHRASES
            if phrase.lower() in current_message.lower()
        )

        if historical_messages:
            corporate_count_historical = sum(
                1 for message in historical_messages
                for phrase in AuthenticityEngine.CORPORATE_PHRASES
                if phrase.lower() in message.lower()
            )
            avg_corporate_historical = corporate_count_historical / len(historical_messages) if historical_messages else 0

            if corporate_count_current > avg_corporate_historical * 2:
                inconsistencies.append({
                    "type": "corporate_language_increase",
                    "previous_avg": avg_corporate_historical,
                    "current": corporate_count_current,
                    "severity": "low",
                })

        personality_score = alignment
        if inconsistencies:
            severity_weights = {"critical": -25, "high": -15, "medium": -10, "low": -5}
            personality_score -= sum(
                severity_weights.get(inc["severity"], -5) for inc in inconsistencies
            )

        return {
            "consistent": personality_score >= 70,
            "personality_score": max(0, min(100, personality_score)),
            "detected_archetype": detected_archetype,
            "declared_archetype": declared_archetype,
            "alignment_with_declared": alignment,
            "inconsistencies": inconsistencies,
            "recommendation": (
                "Personality aligned" if personality_score >= 70
                else f"Address inconsistencies: {'; '.join(inc['type'] for inc in inconsistencies[:2])}"
            ),
        }

    @staticmethod
    def _analyze_tone(text: str) -> Dict[str, Any]:
        """Analyze tone characteristics."""

        formality_keywords = {
            "formal": ["hereby", "therefore", "moreover", "pursuant", "aforementioned"],
            "casual": ["yeah", "gonna", "kinda", "totally", "super"],
            "warm": ["love", "wonderful", "beautiful", "amazing", "appreciate"],
            "cold": ["must", "required", "mandatory", "shall", "forbidden"],
        }

        scores = {style: 0 for style in formality_keywords}
        for style, keywords in formality_keywords.items():
            scores[style] = sum(1 for kw in keywords if kw in text.lower())

        # Calculate formality score (0-100)
        formal_count = scores["formal"]
        casual_count = scores["casual"]
        total = formal_count + casual_count

        if total == 0:
            formality = 50  # Neutral
        else:
            formality = (formal_count / total) * 100

        return {
            "formality": formality,
            "warmth": scores["warm"],
            "coldness": scores["cold"],
            "style_scores": scores,
        }

    @staticmethod
    def check_tone_authenticity(
        message: str,
        expected_tone: str,
    ) -> Dict[str, Any]:
        """
        Check if tone is authentic vs corporate/robotic.

        Returns:
            {
                "authentic": bool,
                "authenticity_score": 0-100,
                "tone_match": bool,
                "corporate_language_detected": [list],
                "improvement": str,
            }
        """

        # Count corporate phrases
        corporate_count = sum(
            1 for phrase in AuthenticityEngine.CORPORATE_PHRASES
            if phrase.lower() in message.lower()
        )

        # Count authentic language
        authentic_count = 0
        for pattern_type, keywords in AuthenticityEngine.AUTHENTIC_PATTERNS.items():
            authentic_count += sum(1 for kw in keywords if kw in message.lower())

        total_phrases = corporate_count + authentic_count
        authenticity_score = 50  # Neutral if no patterns

        if total_phrases > 0:
            authenticity_score = (authentic_count / total_phrases) * 100

        # Check tone match
        tone_profile = AuthenticityEngine._analyze_tone(message)
        tone_match = False

        if expected_tone == "casual":
            tone_match = tone_profile["formality"] < 40
        elif expected_tone == "professional":
            tone_match = 40 <= tone_profile["formality"] <= 70
        elif expected_tone == "warm":
            tone_match = tone_profile["warmth"] > 2
        elif expected_tone == "formal":
            tone_match = tone_profile["formality"] > 70

        # List detected corporate phrases
        corporate_detected = [
            phrase for phrase in AuthenticityEngine.CORPORATE_PHRASES
            if phrase.lower() in message.lower()
        ]

        improvement = ""
        if not tone_match:
            if expected_tone == "casual" and tone_profile["formality"] >= 40:
                improvement = "Use more conversational language: 'yeah', 'honestly', 'totally'"
            elif expected_tone == "warm" and tone_profile["warmth"] == 0:
                improvement = "Add warmth: 'love', 'appreciate', 'care about'"
            elif corporate_detected:
                improvement = f"Avoid corporate speak: {', '.join(corporate_detected[:3])}"

        return {
            "authentic": authenticity_score >= 60 and tone_match,
            "authenticity_score": int(authenticity_score),
            "tone_match": tone_match,
            "expected_tone": expected_tone,
            "corporate_language_detected": corporate_detected,
            "authentic_patterns": {
                k: sum(1 for kw in v if kw in message.lower())
                for k, v in AuthenticityEngine.AUTHENTIC_PATTERNS.items()
            },
            "improvement": improvement,
        }

    @staticmethod
    def validate_stories(
        story: Dict[str, Any],
        story_database: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Validate if story is real (not fabricated fiction).

        Checks:
        1. Story already told (not repeated too often)
        2. Details are specific (not generic)
        3. Conflicts are realistic
        4. Character names match historical usage
        5. Timeline is consistent
        """

        validation = {
            "story_id": story.get("id"),
            "story_title": story.get("title"),
            "likely_real": True,
            "red_flags": [],
            "confidence": 80,
        }

        story_text = story.get("text", "").lower()
        story_date = story.get("date_occurred")

        # Red flag 1: Too generic
        generic_phrases = [
            "I remember this one time",
            "so funny story",
            "you won't believe what happened",
            "I'll never forget",
        ]
        if any(phrase in story_text for phrase in generic_phrases):
            validation["red_flags"].append({
                "type": "generic_opening",
                "message": "Story starts with generic phrase",
                "severity": "low",
            })
            validation["confidence"] -= 10

        # Red flag 2: Perfect ending
        perfect_ending_phrases = ["and we all lived happily", "and that's how we became friends"]
        if any(phrase in story_text for phrase in perfect_ending_phrases):
            validation["red_flags"].append({
                "type": "too_perfect_ending",
                "message": "Ending seems too neat",
                "severity": "medium",
            })
            validation["confidence"] -= 15

        # Red flag 3: Lots of dialogue (often fabricated)
        dialogue_density = story_text.count('"') / len(story_text.split())
        if dialogue_density > 0.1:
            validation["red_flags"].append({
                "type": "high_dialogue_density",
                "message": "Very high dialogue-to-narrative ratio",
                "severity": "low",
            })

        # Red flag 4: Embellishment indicators
        exaggeration_words = ["literally", "absolutely", "insanely", "totally", "completely"]
        exaggeration_count = sum(
            1 for word in exaggeration_words if f" {word} " in f" {story_text} "
        )
        if exaggeration_count > 3:
            validation["red_flags"].append({
                "type": "excessive_embellishment",
                "message": f"Story uses {exaggeration_count} intensifiers",
                "severity": "low",
            })
            validation["confidence"] -= 5

        # Check 5: Timeline consistency
        if story_date:
            present_dates = story.get("mentioned_dates", [])
            if any(date > story_date for date in present_dates):
                validation["red_flags"].append({
                    "type": "timeline_inconsistency",
                    "message": "Story mentions future events",
                    "severity": "high",
                })
                validation["likely_real"] = False
                validation["confidence"] -= 30

        # Check 6: Repeated story (overuse)
        if story_database:
            similar_stories = [s for s in story_database if s.get("theme") == story.get("theme")]
            if len(similar_stories) > 5:
                validation["red_flags"].append({
                    "type": "overused_story",
                    "message": f"Similar story told {len(similar_stories)} times",
                    "severity": "medium",
                })
                validation["confidence"] -= 10

        validation["confidence"] = max(0, min(100, validation["confidence"]))

        return validation

    @staticmethod
    def check_vulnerability(message: str) -> Dict[str, Any]:
        """
        Check if message shows healthy vulnerability (admits limits).

        Returns:
            {
                "shows_vulnerability": bool,
                "vulnerability_score": 0-100,
                "admissions": [list],
                "assessment": str,
            }
        """

        vulnerability_indicators = {
            "struggle": ["struggle", "difficult", "challenge", "hard time"],
            "mistake": ["mistake", "failed", "messed up", "wrong"],
            "limitation": ["don't know", "can't", "not expert", "limited"],
            "learning": ["learned", "discovered", "realized", "evolved"],
            "emotion": ["scared", "uncertain", "nervous", "vulnerable"],
        }

        admissions = []
        for admission_type, keywords in vulnerability_indicators.items():
            for keyword in keywords:
                if keyword in message.lower():
                    admissions.append({
                        "type": admission_type,
                        "keyword": keyword,
                    })

        vulnerability_score = min(100, len(admissions) * 15)

        assessment = ""
        if vulnerability_score == 0:
            assessment = "No vulnerability shown - may seem inauthentic"
        elif vulnerability_score < 30:
            assessment = "Limited vulnerability - could be more authentic"
        elif vulnerability_score < 70:
            assessment = "Healthy vulnerability - authentic and relatable"
        else:
            assessment = "Strong vulnerability - shows genuine authenticity"

        return {
            "shows_vulnerability": len(admissions) > 0,
            "vulnerability_score": vulnerability_score,
            "admission_count": len(admissions),
            "admissions": admissions,
            "assessment": assessment,
        }

    @staticmethod
    def check_growth_mindset(message: str) -> Dict[str, Any]:
        """
        Check if message demonstrates growth mindset.

        Returns:
            {
                "growth_mindset": bool,
                "growth_score": 0-100,
                "indicators": [list],
            }
        """

        growth_indicators = {
            "progress": ["improved", "evolved", "progressed", "advanced"],
            "learning": ["learned", "discovered", "realized", "understood"],
            "resilience": ["bounced back", "recovered", "persevered", "pushed through"],
            "effort": ["worked hard", "dedicated", "invested", "committed"],
            "possibility": ["can grow", "potential", "possible", "achievable"],
        }

        found_indicators = []
        for indicator_type, keywords in growth_indicators.items():
            for keyword in keywords:
                if keyword in message.lower():
                    found_indicators.append({
                        "type": indicator_type,
                        "keyword": keyword,
                    })

        growth_score = min(100, len(found_indicators) * 18)

        return {
            "growth_mindset": growth_score >= 50,
            "growth_score": growth_score,
            "indicator_count": len(found_indicators),
            "indicators": found_indicators,
            "assessment": (
                "Strong growth mindset" if growth_score >= 70
                else "Limited growth mindset" if growth_score < 30
                else "Moderate growth mindset"
            ),
        }

    @staticmethod
    def authenticity_score(
        message: str,
        personality: Dict[str, Any],
        historical_messages: List[str],
        story: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Overall authenticity score (0-100).

        Factors:
        - Personality consistency (30%)
        - Tone authenticity (25%)
        - Vulnerability (20%)
        - Growth mindset (15%)
        - Story validity (10%)
        """

        score = 50  # Neutral baseline

        # Personality consistency
        personality_check = AuthenticityEngine.check_personality_consistency(
            message, historical_messages, personality
        )
        score += (personality_check["personality_score"] - 50) * 0.30

        # Tone authenticity
        expected_tone = personality.get("tone", "warm")
        tone_check = AuthenticityEngine.check_tone_authenticity(message, expected_tone)
        score += (tone_check["authenticity_score"] - 50) * 0.25

        # Vulnerability
        vulnerability_check = AuthenticityEngine.check_vulnerability(message)
        score += (vulnerability_check["vulnerability_score"] - 50) * 0.20

        # Growth mindset
        growth_check = AuthenticityEngine.check_growth_mindset(message)
        score += (growth_check["growth_score"] - 50) * 0.15

        # Story validity (if story provided)
        story_score = 50
        if story:
            story_check = AuthenticityEngine.validate_stories(story, [])
            story_score = story_check["confidence"]
            score += (story_score - 50) * 0.10

        score = max(0, min(100, score))

        return {
            "authenticity_score": int(score),
            "passed": score >= 70,
            "components": {
                "personality_consistency": personality_check["personality_score"],
                "tone_authenticity": tone_check["authenticity_score"],
                "vulnerability": vulnerability_check["vulnerability_score"],
                "growth_mindset": growth_check["growth_score"],
                "story_validity": story_score,
            },
            "issues": (
                personality_check.get("inconsistencies", []) +
                ([d for d in tone_check.get("corporate_language_detected", [])][:2])
            ),
            "recommendations": [
                tone_check.get("improvement", ""),
                vulnerability_check.get("assessment", ""),
                growth_check.get("assessment", ""),
            ],
        }
