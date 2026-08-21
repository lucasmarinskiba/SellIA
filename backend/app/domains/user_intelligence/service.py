"""Phase X9: AI User Intelligence Agent Service."""
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.user_intelligence.models import UserRiskProfile, UserJourneyStage, UserPersonalityType


class UserIntelligenceAgent:
    """AI agent for deep user profiling & journey mapping."""

    @staticmethod
    async def profile_user(
        db: AsyncSession,
        user_id: str,
        email: str,
        company_name: str,
        engagement_data: dict,  # {email_opens, clicks, content_views, demo_requests}
        company_data: dict,  # {industry, company_size, revenue_range, role}
    ) -> UserRiskProfile:
        """Create comprehensive user profile from behavior + firmographic data."""

        # Personality type inference from behavior
        email_open_rate = engagement_data.get("email_opens", 0) / max(engagement_data.get("emails_sent", 1), 1)
        clicks_per_email = engagement_data.get("clicks", 0) / max(engagement_data.get("emails_sent", 1), 1)
        case_study_views = engagement_data.get("case_study_views", 0)
        demo_requests = engagement_data.get("demo_requests", 0)

        # Determine personality type
        if demo_requests >= 2:
            personality = UserPersonalityType.PRAGMATIST
        elif case_study_views >= 3:
            personality = UserPersonalityType.ANALYST
        elif email_open_rate > 0.5 and clicks_per_email > 0.3:
            personality = UserPersonalityType.IMPULSE_BUYER
        elif company_data.get("company_size") in ["enterprise", "1000+"]:
            personality = UserPersonalityType.SKEPTIC
        else:
            personality = UserPersonalityType.EARLY_ADOPTER

        # Infer primary motivation from company data
        role = company_data.get("role", "").lower()
        industry = company_data.get("industry", "").lower()
        if "sales" in role or "revenue" in role:
            primary_motivation = "revenue_growth"
        elif "ops" in role or "efficiency" in role:
            primary_motivation = "time_saving"
        else:
            primary_motivation = "competitive_advantage"

        # Risk scores (higher = more responsive to certain tactics)
        risk_aversion = 7.0 if company_data.get("company_size") == "enterprise" else 4.0
        decision_velocity = 8.0 if personality == UserPersonalityType.IMPULSE_BUYER else 4.0
        social_proof_sensitivity = 7.0 if "mid-market" in company_data.get("company_size", "") else 5.0
        scarcity_responsiveness = 8.0 if email_open_rate > 0.6 else 5.0
        exclusivity_appeal = 7.0 if company_data.get("budget_approved") else 4.0

        # Estimate conversion probability
        engagement_score = (email_open_rate * 0.3 + clicks_per_email * 0.3 + case_study_views * 0.2 + demo_requests * 0.2)
        conversion_prob = min(engagement_score * 0.3, 0.95)

        # Next best action recommendation
        if demo_requests == 0 and case_study_views >= 2:
            next_action = "invite_to_demo"
        elif email_open_rate > 0.5 and clicks_per_email < 0.2:
            next_action = "send_case_study"
        elif company_data.get("budget_approved"):
            next_action = "schedule_call"
        else:
            next_action = "send_ebook"

        # Recommended messaging
        if personality == UserPersonalityType.SKEPTIC:
            messaging = "ROI-focused with third-party validation"
        elif personality == UserPersonalityType.IMPULSE_BUYER:
            messaging = "Scarcity + social proof + exclusive offer"
        elif personality == UserPersonalityType.ANALYST:
            messaging = "Data-heavy case study + competitive comparison"
        else:
            messaging = "Innovation-focused + early-adopter benefits"

        profile = UserRiskProfile(
            user_id=user_id,
            email=email,
            company_name=company_name,
            personality_type=personality,
            risk_aversion_score=risk_aversion,
            decision_velocity=decision_velocity,
            social_proof_sensitivity=social_proof_sensitivity,
            primary_motivation=primary_motivation,
            secondary_motivations=["cost_reduction", "team_productivity"],
            email_open_rate=email_open_rate,
            click_through_rate=clicks_per_email,
            demo_interest_level=demo_requests / 5.0,
            scarcity_responsiveness=scarcity_responsiveness,
            exclusivity_appeal=exclusivity_appeal,
            estimated_conversion_probability=conversion_prob,
            recommended_messaging=messaging,
            next_best_action=next_action,
        )
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
        return profile

    @staticmethod
    async def get_personalized_messaging(profile: UserRiskProfile) -> dict:
        """Generate personalized messaging based on user profile."""
        personality = profile.personality_type

        messages = {
            "early_adopter": {
                "subject": "Be first: Exclusive early-access opportunity for innovation leaders",
                "hook": "Join the 2% of companies leading the AI revolution",
                "cta": "Get early-access"
            },
            "pragmatist": {
                "subject": "See the ROI: $2.3M avg revenue increase in 6 months",
                "hook": "Financial impact proven in 500+ companies like yours",
                "cta": "View ROI calculator"
            },
            "skeptic": {
                "subject": "Enterprise-grade proof: Validated by Gartner + Forrester",
                "hook": "See peer reviews + analyst reports from industry leaders",
                "cta": "Read analyst report"
            },
            "impulse_buyer": {
                "subject": "Last slot: Only 3 seats left in cohort ending Friday",
                "hook": "Limited-time 40% founding member discount (24 hours)",
                "cta": "Claim your spot"
            },
            "analyst": {
                "subject": "Deep dive: 87-page technical breakdown vs. competitors",
                "hook": "Feature-by-feature comparison with implementation details",
                "cta": "Download comparison"
            },
            "social_proof_seeker": {
                "subject": "Join Slack, HubSpot, Salesforce teams using SellIA",
                "hook": "See how Fortune 500 companies are scaling with us",
                "cta": "Watch case study"
            },
            "status_conscious": {
                "subject": "VIP: Exclusive invite to CEO roundtable + private training",
                "hook": "Premium tier reserved for top-performing companies only",
                "cta": "Request VIP access"
            },
            "value_maximizer": {
                "subject": "Compare pricing: SellIA vs. 5 alternatives (full breakdown)",
                "hook": "See why 73% choose us for better value per feature",
                "cta": "See pricing comparison"
            }
        }

        return messages.get(personality, messages["pragmatist"])

    @staticmethod
    async def update_journey_stage(
        db: AsyncSession,
        user_id: str,
        new_stage: str,
    ) -> UserJourneyStage:
        """Move user to next stage with momentum tracking."""
        stage = UserJourneyStage(
            user_id=user_id,
            stage=new_stage,
            entry_date=datetime.now(timezone.utc),
            momentum="accelerating",
        )
        db.add(stage)
        await db.commit()
        await db.refresh(stage)
        return stage

    @staticmethod
    def calculate_churn_risk(profile: UserRiskProfile) -> float:
        """Predict churn probability for existing customers (0-1.0)."""
        # Factors: low engagement, long time since last action, support tickets, price sensitivity
        engagement = profile.email_open_rate + profile.click_through_rate
        engagement_risk = 1.0 - (engagement / 2.0)  # 0 if high engagement, 1 if no engagement
        return min(engagement_risk, 1.0)
