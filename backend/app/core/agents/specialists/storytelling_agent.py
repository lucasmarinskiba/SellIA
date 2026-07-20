"""
Storytelling Agent — Brand storytelling and communication frameworks.

Specialties:
- Brand storytelling (origin, mission, customer stories)
- Communication frameworks (Hero's Journey, Pixar, TED)
- Pitch decks and investor narratives
- Customer case studies and testimonials
"""

import logging
from typing import Dict, List, Any, Optional
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class StoryType(str, Enum):
    """Types of stories."""
    ORIGIN = "origin"  # How company started
    MISSION = "mission"  # What company stands for
    CUSTOMER = "customer"  # Customer success story
    PROBLEM_SOLUTION = "problem_solution"  # Problem and how you solved it
    MARKET_INSIGHT = "market_insight"  # Trend or insight story
    JOURNEY = "journey"  # Transformation story


class CommunicationFramework(str, Enum):
    """Communication story frameworks."""
    HEROS_JOURNEY = "heros_journey"  # Hero's Journey framework
    PIXAR = "pixar"  # Pixar story structure
    TED = "ted"  # TED talk structure
    PROBLEM_SOLUTION = "problem_solution"  # Simple problem-solution arc
    TRANSFORMATION = "transformation"  # Before-after-bridge


class StorytellingAgent:
    """Expert in storytelling and communication."""

    HEROS_JOURNEY = {
        "structure": [
            {
                "stage": "1. Ordinary World",
                "description": "Hero's normal life before adventure",
                "in_pitch": "Market before your solution - status quo",
                "example": "Customers manually tracking expenses in spreadsheets",
            },
            {
                "stage": "2. Call to Adventure",
                "description": "Challenge or quest appears",
                "in_pitch": "The problem that needs solving",
                "example": "Expense tracking is manual, error-prone, time-consuming",
            },
            {
                "stage": "3. Refusal of Call",
                "description": "Hero hesitates or refuses",
                "in_pitch": "Barriers to adoption (skepticism, inertia)",
                "example": "People are skeptical new tools will be better",
            },
            {
                "stage": "4. Meeting the Mentor",
                "description": "Mentor appears with wisdom/tools",
                "in_pitch": "Your solution arrives to help",
                "example": "We built automated expense tracking software",
            },
            {
                "stage": "5. Crossing the Threshold",
                "description": "Hero commits to the quest",
                "in_pitch": "Customer adopts your solution",
                "example": "First users start tracking automatically",
            },
            {
                "stage": "6. Tests, Allies, Enemies",
                "description": "Hero faces challenges and learns",
                "in_pitch": "Challenges overcome with your help",
                "example": "Integration challenges solved by our team",
            },
            {
                "stage": "7. Approach to Inmost Cave",
                "description": "Preparation for major challenge",
                "in_pitch": "Getting maximum value from your solution",
                "example": "Setting up automated workflows",
            },
            {
                "stage": "8. The Ordeal",
                "description": "Major life-or-death moment",
                "in_pitch": "Critical moment of truth",
                "example": "Tax deadline approaching with accurate data",
            },
            {
                "stage": "9. Reward",
                "description": "Hero survives and gets prize",
                "in_pitch": "The benefits realized",
                "example": "Perfect expense records, audit-ready, saved 10 hours/week",
            },
            {
                "stage": "10. The Road Back",
                "description": "Hero returns home",
                "in_pitch": "Customer success and new baseline",
                "example": "Back to normal but with better processes",
            },
            {
                "stage": "11. Resurrection",
                "description": "Final test using all learned lessons",
                "in_pitch": "Expanded use cases",
                "example": "Now tracking company expenses too",
            },
            {
                "stage": "12. Return with Elixir",
                "description": "Hero brings wisdom back",
                "in_pitch": "Customer becomes advocate/case study",
                "example": "Customer tells others about their transformation",
            },
        ],
    }

    PIXAR_STRUCTURE = {
        "formula": "Once upon a time... Every day... One day... Because of that... Because of that... Until finally... And the moral is...",
        "breakdown": [
            {
                "element": "Once upon a time",
                "description": "The setup - who is the main character?",
                "pitch_use": "Introduce the protagonist (customer/market)",
            },
            {
                "element": "Every day (their life)",
                "description": "Normal routine/pattern",
                "pitch_use": "The status quo and routine",
            },
            {
                "element": "One day (everything changed)",
                "description": "Inciting incident - what disrupts?",
                "pitch_use": "The problem or trigger",
            },
            {
                "element": "Because of that (consequence 1)",
                "description": "First consequence of the change",
                "pitch_use": "Escalating problem/challenge",
            },
            {
                "element": "And because of that (consequence 2)",
                "description": "Second consequence builds",
                "pitch_use": "Problem compounds",
            },
            {
                "element": "Until finally (climax)",
                "description": "The turning point",
                "pitch_use": "Your solution enters",
            },
            {
                "element": "And the moral is (lesson)",
                "description": "The lesson/transformation",
                "pitch_use": "The new way/benefit",
            },
        ],
    }

    TED_TALK_STRUCTURE = {
        "elements": [
            {
                "section": "Hook (first 30 seconds)",
                "purpose": "Grab attention immediately",
                "techniques": [
                    "Surprising statistic",
                    "Bold question",
                    "Personal story",
                    "Relevant quote",
                ],
                "example": "1 in 3 companies fail in first 5 years. But why?",
            },
            {
                "section": "Credibility (first 2 minutes)",
                "purpose": "Establish why you should listen",
                "techniques": [
                    "Personal experience",
                    "Research/data",
                    "Relevant background",
                ],
            },
            {
                "section": "Problem (first 5 minutes)",
                "purpose": "Help audience feel the problem",
                "techniques": [
                    "Specific examples",
                    "Data/research",
                    "Emotional connection",
                ],
            },
            {
                "section": "Insight (middle)",
                "purpose": "Share the key insight/idea",
                "techniques": [
                    "Clear articulation",
                    "Surprising twist",
                    "Visual explanation",
                ],
            },
            {
                "section": "Evidence (latter half)",
                "purpose": "Prove the idea works",
                "techniques": [
                    "Case studies",
                    "Data/research",
                    "Demonstrations",
                ],
            },
            {
                "section": "Call to Action (last minute)",
                "purpose": "What should audience do?",
                "techniques": [
                    "Clear ask",
                    "Inspiring vision",
                    "Memorable close",
                ],
            },
        ],
        "pacing": "Slow, conversational, with pauses",
        "visuals": "Minimal, high-quality, support story",
    }

    CUSTOMER_STORY_FRAMEWORK = {
        "hero": {
            "focus": "Customer is the hero, not you",
            "elements": [
                "Customer name and role",
                "Their goal/challenge",
                "Their industry/context",
            ],
        },
        "situation": {
            "before": [
                "What was the problem/challenge?",
                "How much did it cost them?",
                "What did they try before?",
                "Why didn't other solutions work?",
            ],
        },
        "challenge": {
            "elements": [
                "Specific pain or struggle",
                "Stakes: what would happen if not solved?",
                "Why existing solutions didn't work",
            ],
        },
        "solution": {
            "your_role": [
                "How they found you",
                "Why they chose you",
                "Implementation (mention challenges overcome)",
            ],
        },
        "results": {
            "quantified": [
                "ROI or cost savings",
                "Time saved",
                "Efficiency gains",
                "Revenue increase",
            ],
            "qualitative": [
                "How they feel now",
                "New capabilities",
                "Confidence/peace of mind",
            ],
        },
        "quote": {
            "element": "Customer testimonial (powerful and specific)",
            "example": "We went from manual tracking to fully automated in 2 weeks. Now we never miss an expense and audit season is stress-free.",
        },
    }

    BRAND_STORY_ARCHETYPES = {
        "origin_story": {
            "elements": [
                "Why founder started company",
                "Personal problem they faced",
                "Insight that led to idea",
                "Early struggles",
                "Breakthrough moment",
            ],
            "tone": "Personal, authentic, humble",
        },
        "underdog_story": {
            "elements": [
                "Odds were against us",
                "What we were up against",
                "How we overcame",
                "Unlikely victory",
            ],
            "tone": "Inspiring, determined",
        },
        "mission_story": {
            "elements": [
                "What we believe",
                "Why it matters",
                "How we're changing the world",
                "Call to join movement",
            ],
            "tone": "Purposeful, inspiring",
        },
        "transformation_story": {
            "elements": [
                "Where we started",
                "Key pivot moment",
                "How we evolved",
                "Where we are now",
            ],
            "tone": "Reflective, growth-oriented",
        },
    }

    PITCH_DECK_STRUCTURE = {
        "slides": [
            {
                "slide": 1,
                "title": "Cover Slide",
                "content": "Company name, tagline, date",
            },
            {
                "slide": 2,
                "title": "Problem",
                "content": "The problem you're solving (customer pain point)",
            },
            {
                "slide": 3,
                "title": "Market Size",
                "content": "TAM, SAM, SOM (Total, Serviceable, Obtainable Market)",
            },
            {
                "slide": 4,
                "title": "Solution",
                "content": "How you solve it (product demo if possible)",
            },
            {
                "slide": 5,
                "title": "Why Now",
                "content": "Market conditions enabling the opportunity",
            },
            {
                "slide": 6,
                "title": "Business Model",
                "content": "How you make money",
            },
            {
                "slide": 7,
                "title": "Traction",
                "content": "Proof points (customers, revenue, growth)",
            },
            {
                "slide": 8,
                "title": "Team",
                "content": "Why your team can execute",
            },
            {
                "slide": 9,
                "title": "Competition",
                "content": "Competitive landscape and differentiation",
            },
            {
                "slide": 10,
                "title": "Financial Projections",
                "content": "3-year revenue projections",
            },
            {
                "slide": 11,
                "title": "Ask",
                "content": "How much you're raising and use of funds",
            },
            {
                "slide": 12,
                "title": "Contact",
                "content": "Your info and call to action",
            },
        ],
    }

    @staticmethod
    def craft_brand_story(
        company_name: str,
        founder_origin: str,
        mission: str,
        target_audience: str
    ) -> Dict[str, Any]:
        """Craft compelling brand story."""
        return {
            "company": company_name,
            "origin": founder_origin,
            "mission": mission,
            "target_audience": target_audience,
            "story_arc": {
                "beginning": "The problem/inspiration",
                "middle": "The journey/development",
                "end": "The transformation/impact",
            },
            "key_messages": [],
            "emotional_elements": [],
            "proof_points": [],
            "narrative": "",
            "variations": {
                "elevator_pitch": "",
                "social_media": "",
                "website_hero": "",
                "investor_pitch": "",
            },
        }

    @staticmethod
    def create_customer_case_study(
        customer_name: str,
        customer_role: str,
        initial_challenge: str,
        solution_provided: str,
        results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create structured customer case study."""
        case_study = StorytellingAgent.CUSTOMER_STORY_FRAMEWORK.copy()
        case_study.update({
            "customer": customer_name,
            "role": customer_role,
            "challenge": initial_challenge,
            "solution": solution_provided,
            "results": results,
            "structure": [
                "1. Introduction (who, what, context)",
                "2. Challenge (problem, stakes, impact)",
                "3. Solution (how we helped, implementation)",
                "4. Results (quantified + qualitative)",
                "5. Quote (testimonial from customer)",
                "6. Call to action (similar customers)",
            ],
            "formats": [
                "1-page PDF",
                "Video testimonial (3-5 min)",
                "Blog post",
                "Case study page on website",
                "LinkedIn article",
            ],
        })

        return case_study

    @staticmethod
    def build_pitch_narrative(
        company: str,
        problem: str,
        solution: str,
        market_size: str,
        target_customer: str
    ) -> Dict[str, Any]:
        """Build compelling pitch narrative."""
        return {
            "company": company,
            "hook": f"Most {target_customer} face [problem]. We're changing that.",
            "problem_statement": problem,
            "solution_value_prop": solution,
            "market_opportunity": market_size,
            "target_customer_profile": target_customer,
            "narrative_flow": [
                "Problem (why this matters)",
                "Market size (opportunity scale)",
                "Solution (why our approach)",
                "Traction (proof it works)",
                "Team (who executes)",
                "Ask (what we need)",
            ],
            "emotional_hooks": [],
            "credibility_markers": [],
            "memorable_takeaway": "",
        }

    @staticmethod
    def design_investor_pitch(
        company: str,
        funding_amount: float,
        use_of_funds: Dict[str, float]
    ) -> Dict[str, Any]:
        """Design investor pitch deck."""
        return {
            "company": company,
            "funding_ask": funding_amount,
            "use_of_funds": use_of_funds,
            "deck_structure": StorytellingAgent.PITCH_DECK_STRUCTURE,
            "storytelling_hooks": [
                "Problem: Make it visceral and relatable",
                "Why now: Market tailwinds",
                "Solution: Clear and compelling",
                "Traction: Real proof points",
                "Team: Founder origin story",
                "Vision: Inspiring future state",
            ],
            "investor_psychology": {
                "principles": [
                    "Invest in people first (team)",
                    "Addressable market size (big opportunity)",
                    "Clear path to profitability",
                    "Defensible advantage",
                ],
                "tell_story_that": [
                    "Shows you understand problem deeply",
                    "Demonstrates founder conviction",
                    "Shows early traction/validation",
                    "Proves repeatable model",
                ],
            },
            "presentation_tips": [
                "Tell story, don't read slides",
                "Use visuals, minimize text",
                "Practice extensively",
                "Expect tough questions",
                "Focus on narrative, not data",
            ],
        }

    @staticmethod
    def apply_heroes_journey(
        protagonist: str,
        ordinary_world: str,
        call_to_adventure: str,
        climax: str,
        resolution: str
    ) -> Dict[str, Any]:
        """Apply Hero's Journey framework to your story."""
        journey = []
        for stage in StorytellingAgent.HEROS_JOURNEY["structure"]:
            journey.append({
                "stage": stage["stage"],
                "description": stage["description"],
                "in_your_story": "",
            })

        return {
            "protagonist": protagonist,
            "ordinary_world": ordinary_world,
            "call_to_adventure": call_to_adventure,
            "climax": climax,
            "resolution": resolution,
            "full_journey": journey,
        }

    @staticmethod
    def create_content_narratives(
        primary_story: str,
        target_segments: List[str]
    ) -> Dict[str, Any]:
        """Create tailored narratives for different audience segments."""
        return {
            "primary_story": primary_story,
            "segment_narratives": [
                {
                    "segment": segment,
                    "angle": f"How this solves problems for {segment}",
                    "messaging": [],
                    "emotional_hook": "",
                    "proof_points": [],
                }
                for segment in target_segments
            ],
            "story_variations": {
                "social_media": "Short, visual, engaging",
                "sales_email": "Benefit-focused, credible",
                "website": "Comprehensive, professional",
                "investor_pitch": "Vision-focused, scalable",
                "employee_talk": "Inspiring, mission-driven",
            },
        }

    @staticmethod
    def storytelling_workshop_guide() -> Dict[str, Any]:
        """Guide for storytelling workshop."""
        return {
            "duration": "Half day",
            "participants": "Marketing, sales, leadership",
            "agenda": [
                {
                    "time": "0:00-0:30",
                    "activity": "Story analysis",
                    "output": "Identify company story elements",
                },
                {
                    "time": "0:30-1:00",
                    "activity": "Brainstorm brand narratives",
                    "output": "3-5 story ideas",
                },
                {
                    "time": "1:00-2:00",
                    "activity": "Customer story workshop",
                    "output": "Draft case study narrative",
                },
                {
                    "time": "2:00-2:30",
                    "activity": "Message mapping",
                    "output": "Consistent messaging across channels",
                },
            ],
            "outputs": [
                "Brand story (500 words)",
                "Key messages (3 pillars, 3 points each)",
                "Customer story template",
                "Pitch narrative (60-second version)",
            ],
        }
