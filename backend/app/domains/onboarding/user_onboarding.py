"""Phase 19: User Onboarding & Setup Wizard."""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class OnboardingStep(str, Enum):
    PROFILE = "profile"
    PRODUCT = "product"
    TARGET = "target"
    CHANNELS = "channels"
    GOALS = "goals"
    COMPLETE = "complete"


@dataclass
class UserOnboardingSession:
    user_id: str
    session_id: str
    current_step: OnboardingStep = OnboardingStep.PROFILE
    profile_complete: bool = False
    product_complete: bool = False
    campaign_created: bool = False
    first_leads_generated: bool = False
    estimated_monthly_leads: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


@dataclass
class OnboardingAnswers:
    # Step 1: Profile
    user_name: str
    user_email: str
    user_phone: str
    company_name: str

    # Step 2: Product
    product_name: str
    product_description: str
    category: str
    unique_value: str

    # Step 3: Target
    target_audience: str
    price_range: str
    geographic_scope: str

    # Step 4: Channels
    preferred_channels: List[str]

    # Step 5: Goals
    monthly_lead_goal: int
    annual_revenue_target: float


class OnboardingEngine:
    """Guide new users through setup"""

    def create_session(self, user_id: str) -> OnboardingSession:
        """Create onboarding session"""
        session_id = f"onb_{user_id}_{datetime.utcnow().timestamp()}"
        return OnboardingSession(user_id=user_id, session_id=session_id)

    def get_step_content(self, step: OnboardingStep) -> Dict[str, Any]:
        """Get questions/content for step"""

        if step == OnboardingStep.PROFILE:
            return {
                "title": "Tell us about yourself",
                "questions": [
                    {"field": "user_name", "label": "Your name", "type": "text"},
                    {"field": "user_email", "label": "Email", "type": "email"},
                    {"field": "user_phone", "label": "Phone", "type": "tel"},
                    {"field": "company_name", "label": "Business name", "type": "text"}
                ],
                "time_minutes": 2
            }

        elif step == OnboardingStep.PRODUCT:
            return {
                "title": "What do you sell/offer?",
                "questions": [
                    {"field": "product_name", "label": "Product/Service name", "type": "text"},
                    {"field": "product_description", "label": "Description (50 words)", "type": "textarea"},
                    {"field": "category", "label": "Category", "type": "select",
                     "options": ["Services", "Products", "Digital", "Consulting", "Other"]},
                    {"field": "unique_value", "label": "What makes you different?", "type": "text"}
                ],
                "time_minutes": 5
            }

        elif step == OnboardingStep.TARGET:
            return {
                "title": "Who are your customers?",
                "questions": [
                    {"field": "target_audience", "label": "Target audience", "type": "textarea"},
                    {"field": "price_range", "label": "Price range", "type": "text"},
                    {"field": "geographic_scope", "label": "Where do you operate?", "type": "text"}
                ],
                "time_minutes": 3
            }

        elif step == OnboardingStep.CHANNELS:
            return {
                "title": "Where to find your customers?",
                "channels": [
                    {"name": "Google Maps", "description": "Local business searches"},
                    {"name": "Instagram", "description": "Visual marketing"},
                    {"name": "LinkedIn", "description": "Professional network"},
                    {"name": "Email", "description": "Direct marketing"},
                    {"name": "WhatsApp", "description": "Direct messaging"},
                    {"name": "Marketplace", "description": "E-commerce platforms"}
                ],
                "time_minutes": 3
            }

        elif step == OnboardingStep.GOALS:
            return {
                "title": "What are your goals?",
                "questions": [
                    {"field": "monthly_lead_goal", "label": "Monthly leads target", "type": "number"},
                    {"field": "annual_revenue_target", "label": "Annual revenue target", "type": "number"}
                ],
                "time_minutes": 2
            }

        return {}

    def complete_step(
        self, session: OnboardingSession, step: OnboardingStep, answers: Dict
    ) -> OnboardingSession:
        """Mark step complete"""

        if step == OnboardingStep.PROFILE:
            session.profile_complete = True
        elif step == OnboardingStep.PRODUCT:
            session.product_complete = True

        # Move to next step
        steps = [OnboardingStep.PROFILE, OnboardingStep.PRODUCT, OnboardingStep.TARGET,
                OnboardingStep.CHANNELS, OnboardingStep.GOALS, OnboardingStep.COMPLETE]
        current_idx = steps.index(step)
        if current_idx < len(steps) - 1:
            session.current_step = steps[current_idx + 1]

        logger.info(f"Onboarding step complete: {step} for {session.user_id}")
        return session

    def finish_onboarding(self, session: OnboardingSession) -> Dict[str, Any]:
        """Complete onboarding"""

        session.current_step = OnboardingStep.COMPLETE
        session.completed_at = datetime.utcnow()

        return {
            "status": "success",
            "message": "Welcome to SellIA!",
            "next_steps": [
                "First lead generation starting automatically",
                "Check your dashboard for leads",
                "Configure your integrations",
                "Start contacting leads"
            ],
            "first_leads_in": "1-2 hours"
        }

    def get_onboarding_progress(self, session: OnboardingSession) -> Dict[str, Any]:
        """Get progress"""

        steps = [OnboardingStep.PROFILE, OnboardingStep.PRODUCT, OnboardingStep.TARGET,
                OnboardingStep.CHANNELS, OnboardingStep.GOALS, OnboardingStep.COMPLETE]
        current_idx = steps.index(session.current_step)
        progress = (current_idx / len(steps)) * 100

        return {
            "progress_percent": progress,
            "current_step": session.current_step.value,
            "completed_steps": steps[:current_idx],
            "remaining_steps": steps[current_idx + 1:],
            "estimated_completion_minutes": 15 - (current_idx * 3)
        }
