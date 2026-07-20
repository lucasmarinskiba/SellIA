"""
SellIA Response Engine — Generates unique, contextual, personality-driven responses.

Modules:
1. comment_analyzer: Sentiment, intent, urgency, audience analysis
2. humor_generator: Context-aware jokes, timing, authenticity
3. educational_responder: Micro-teaching, resources, FAQ
4. engagement_optimizer: Hooks, CTAs, follow-ups, timing
5. personality_injector: Brand voice, variation, authenticity
6. comment_response_engine: Orchestrator - ties everything together
"""

from .comment_analyzer import CommentAnalyzer
from .humor_generator import HumorGenerator
from .educational_responder import EducationalResponder
from .engagement_optimizer import EngagementOptimizer
from .personality_injector import PersonalityInjector
from .comment_response_engine import CommentResponseEngine

__all__ = [
    "CommentAnalyzer",
    "HumorGenerator",
    "EducationalResponder",
    "EngagementOptimizer",
    "PersonalityInjector",
    "CommentResponseEngine",
]
