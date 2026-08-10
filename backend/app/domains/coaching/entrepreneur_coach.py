"""Phase 23: Entrepreneurship Coach Agent - guides new entrepreneurs."""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class EntrepreneurStage(str, Enum):
    DAY_1 = "day_1"
    WEEK_1 = "week_1"
    MONTH_1 = "month_1"
    MONTH_3 = "month_3"
    MONTH_6 = "month_6"
    YEAR_1 = "year_1"
    SCALING = "scaling"


class CoachingTopic(str, Enum):
    GETTING_STARTED = "getting_started"
    FIRST_LEAD = "first_lead"
    FIRST_SALE = "first_sale"
    PRICING = "pricing"
    MARKETING = "marketing"
    SCALING = "scaling"
    HIRING = "hiring"
    MINDSET = "mindset"
    EMERGENCY = "emergency"


@dataclass
class EntrepreneurProfile:
    user_id: str
    stage: EntrepreneurStage
    days_in_business: int
    leads_generated: int = 0
    deals_closed: int = 0
    revenue: float = 0.0
    team_size: int = 1
    motivation_level: float = 0.8  # 0-1
    challenges: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CoachingMessage:
    title: str
    body: str
    topic: CoachingTopic
    urgency: str  # high, normal, low
    action_item: str
    resource_url: Optional[str] = None


class EntrepreneurCoachAgent:
    """Coach that motivates and guides new entrepreneurs"""

    def __init__(self):
        self.profiles: Dict[str, EntrepreneurProfile] = {}

    def assess_entrepreneur(self, user_id: str, business_data: Dict[str, Any]) -> EntrepreneurProfile:
        """Assess entrepreneur's stage and create profile"""

        days_in_business = business_data.get("days_in_business", 0)
        leads = business_data.get("leads_generated", 0)
        deals = business_data.get("deals_closed", 0)
        revenue = business_data.get("revenue", 0.0)

        # Determine stage
        if days_in_business < 1:
            stage = EntrepreneurStage.DAY_1
        elif days_in_business < 7:
            stage = EntrepreneurStage.WEEK_1
        elif days_in_business < 30:
            stage = EntrepreneurStage.MONTH_1
        elif days_in_business < 90:
            stage = EntrepreneurStage.MONTH_3
        elif days_in_business < 180:
            stage = EntrepreneurStage.MONTH_6
        elif days_in_business < 365:
            stage = EntrepreneurStage.YEAR_1
        else:
            stage = EntrepreneurStage.SCALING

        profile = EntrepreneurProfile(
            user_id=user_id,
            stage=stage,
            days_in_business=days_in_business,
            leads_generated=leads,
            deals_closed=deals,
            revenue=revenue
        )

        # Identify challenges
        if leads == 0 and days_in_business > 3:
            profile.challenges.append("No leads yet")
        if deals == 0 and leads > 0:
            profile.challenges.append("Leads not converting")
        if revenue == 0 and days_in_business > 7:
            profile.challenges.append("No revenue")

        self.profiles[user_id] = profile
        logger.info(f"Entrepreneur profile assessed: {user_id} - Stage: {stage.value}")

        return profile

    def get_daily_coaching(self, user_id: str) -> CoachingMessage:
        """Get personalized daily coaching message"""

        if user_id not in self.profiles:
            return self._get_default_message()

        profile = self.profiles[user_id]

        # Emergency: no sales in critical period
        if profile.deals_closed == 0 and profile.days_in_business > 14:
            return self._get_emergency_message(profile)

        # First lead celebration
        if profile.leads_generated == 1:
            return self._get_first_lead_message()

        # First sale celebration
        if profile.deals_closed == 1:
            return self._get_first_sale_message()

        # Stage-specific coaching
        if profile.stage == EntrepreneurStage.DAY_1:
            return self._get_day1_message()
        elif profile.stage == EntrepreneurStage.WEEK_1:
            return self._get_week1_message()
        elif profile.stage == EntrepreneurStage.MONTH_1:
            return self._get_month1_message()
        else:
            return self._get_scaling_message(profile)

    def _get_emergency_message(self, profile: EntrepreneurProfile) -> CoachingMessage:
        """Emergency message for entrepreneurs struggling"""

        return CoachingMessage(
            title="You Got This! - Emergency Support",
            body=f"Hey! I notice you haven't closed a deal yet after {profile.days_in_business} days. "
                 "This is NORMAL - most entrepreneurs take 2-4 weeks for first sale. "
                 "Let's fix this together RIGHT NOW:\n\n"
                 "1. Are you contacting enough leads? (Need at least 20/day)\n"
                 "2. What's your message? (Demo it to 3 friends today)\n"
                 "3. Are you following up? (Most sales = 3rd contact)",
            topic=CoachingTopic.EMERGENCY,
            urgency="high",
            action_item="Contact 20 leads TODAY + follow up with yesterday's leads",
            resource_url="https://sellia.ai/emergency-sales-guide"
        )

    def _get_first_lead_message(self) -> CoachingMessage:
        """Celebrate first lead"""

        return CoachingMessage(
            title="FIRST LEAD! You're Doing It!",
            body="CONGRATS! You got your FIRST LEAD! This is HUGE. "
                 "This proves people want what you're selling.\n\n"
                 "Now let's convert them:\n"
                 "1. Follow up within 2 hours (you're hot!)\n"
                 "2. Offer a demo/consultation/sample\n"
                 "3. Close the deal - ask for the sale",
            topic=CoachingTopic.FIRST_LEAD,
            urgency="high",
            action_item="Follow up with your lead TODAY - within 2 hours!"
        )

    def _get_first_sale_message(self) -> CoachingMessage:
        """Celebrate first sale"""

        return CoachingMessage(
            title="FIRST SALE!!! You're OFFICIALLY a business owner!",
            body="🎉 YOU DID IT! You closed your FIRST DEAL! "
                 "You're now officially an entrepreneur making money!\n\n"
                 "Now replicate it:\n"
                 "1. Document EXACTLY how you got this sale\n"
                 "2. Do it again 9 more times (10 sales = sustainable)\n"
                 "3. Celebrate with your family!",
            topic=CoachingTopic.FIRST_SALE,
            urgency="normal",
            action_item="Get 9 more sales this month! You know it works!"
        )

    def _get_day1_message(self) -> CoachingMessage:
        """Day 1 motivation and setup"""

        return CoachingMessage(
            title="Welcome to Your Journey!",
            body="Day 1 of your business! Exciting! 🚀\n\n"
                 "Your mission: Get 1 lead by end of today.\n\n"
                 "Here's what to do RIGHT NOW:\n"
                 "1. Tell 10 people you know what you're selling\n"
                 "2. Set up your basic presence (Google Maps, Instagram)\n"
                 "3. Get your first lead - even from friends is OK!",
            topic=CoachingTopic.GETTING_STARTED,
            urgency="high",
            action_item="Get 1 lead today - reach out to 10 people"
        )

    def _get_week1_message(self) -> CoachingMessage:
        """Week 1 momentum building"""

        return CoachingMessage(
            title="Week 1 Momentum - Keep Going!",
            body="You've lasted a WHOLE WEEK! Most people quit. You're different.\n\n"
                 "This week's goal: Get 10 leads.\n\n"
                 "Do this:\n"
                 "1. Contact 2 people/day (10 by Friday)\n"
                 "2. Track responses\n"
                 "3. Improve your pitch based on feedback",
            topic=CoachingTopic.MARKETING,
            urgency="normal",
            action_item="Get 10 leads this week"
        )

    def _get_month1_message(self) -> CoachingMessage:
        """Month 1 critical milestone"""

        return CoachingMessage(
            title="Month 1 Critical Milestone!",
            body="You've been at this for a MONTH! Most quit at week 2. You're winning.\n\n"
                 "Your challenge: Get your FIRST SALE by day 30.\n\n"
                 "Strategy:\n"
                 "1. You have leads - now SELL\n"
                 "2. Lower your price if needed (get proof it works)\n"
                 "3. Follow up relentlessly",
            topic=CoachingTopic.FIRST_SALE,
            urgency="high",
            action_item="Close your first deal THIS MONTH"
        )

    def _get_scaling_message(self, profile: EntrepreneurProfile) -> CoachingMessage:
        """Scaling message for established businesses"""

        return CoachingMessage(
            title="Time to Scale!",
            body=f"You've built something real! ${profile.revenue:,.0f} in revenue proves it.\n\n"
                 "Your mission: 10x your business.\n\n"
                 "Options:\n"
                 "1. Automate lead generation (you're doing it)\n"
                 "2. Hire your first team member\n"
                 "3. Expand to new markets/products",
            topic=CoachingTopic.SCALING,
            urgency="normal",
            action_item="Choose one: automation, hiring, or expansion"
        )

    def _get_default_message(self) -> CoachingMessage:
        """Default message for unknown profiles"""

        return CoachingMessage(
            title="Welcome to SellIA!",
            body="Let's build your business together!\n\n"
                 "First steps:\n"
                 "1. Tell us what you sell\n"
                 "2. Get your first lead\n"
                 "3. Make your first sale\n\n"
                 "You've got this!",
            topic=CoachingTopic.GETTING_STARTED,
            urgency="normal",
            action_item="Complete your profile and get started"
        )

    def get_milestone_tracking(self, user_id: str) -> Dict[str, Any]:
        """Track entrepreneur milestones"""

        if user_id not in self.profiles:
            return {}

        profile = self.profiles[user_id]

        milestones = [
            {"milestone": "Business started", "achieved": True, "date": profile.created_at.isoformat()},
            {"milestone": "First lead", "achieved": profile.leads_generated >= 1, "target": 1},
            {"milestone": "10 leads", "achieved": profile.leads_generated >= 10, "target": 10},
            {"milestone": "First sale", "achieved": profile.deals_closed >= 1, "target": 1},
            {"milestone": "5 sales", "achieved": profile.deals_closed >= 5, "target": 5},
            {"milestone": "$1000 revenue", "achieved": profile.revenue >= 1000, "target": 1000},
            {"milestone": "Hire first employee", "achieved": profile.team_size > 1, "target": 2},
        ]

        return {
            "user_id": user_id,
            "stage": profile.stage.value,
            "milestones": milestones,
            "next_milestone": self._get_next_milestone(profile)
        }

    def _get_next_milestone(self, profile: EntrepreneurProfile) -> Dict[str, Any]:
        """Get next milestone to achieve"""

        if profile.deals_closed == 0:
            return {
                "milestone": "First Sale",
                "description": "Close your first deal",
                "priority": "CRITICAL",
                "deadline_days": 30 - profile.days_in_business
            }
        elif profile.deals_closed < 5:
            return {
                "milestone": "5 Sales",
                "description": "Prove your business model works",
                "priority": "HIGH",
                "progress": f"{profile.deals_closed}/5"
            }
        elif profile.revenue < 5000:
            return {
                "milestone": "$5000 Revenue",
                "description": "Build momentum and cover costs",
                "priority": "HIGH",
                "progress": f"${profile.revenue:,.0f}/$5000"
            }
        else:
            return {
                "milestone": "Hire First Person",
                "description": "Scale beyond yourself",
                "priority": "MEDIUM"
            }
