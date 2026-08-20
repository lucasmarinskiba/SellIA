"""Phase 2: ML Pipeline Service - Predictive Models."""
from typing import Optional
from uuid import UUID
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.domains.ml_pipelines.models import LeadScoringModel, ChurnPredictionModel, CLVModel, ChannelRoutingModel


class MLPipelineService:
    @staticmethod
    async def score_lead(
        db: AsyncSession,
        business_id: UUID,
        customer_id: UUID,
        engagement_score: float,
        email_opens: int,
        email_clicks: int,
        phone_calls: int,
        demo_attended: bool,
        website_visits: int,
        pages_viewed: int,
        time_on_site_minutes: float,
    ) -> LeadScoringModel:
        """Calculate lead score using ML model."""
        # Weighted scoring (simplified ML logic)
        weights = {
            "engagement": 0.2,
            "email": 0.15,
            "phone": 0.15,
            "demo": 0.25,
            "website": 0.25,
        }

        # Normalize features (0-100)
        engagement = engagement_score
        email_score = min((email_opens * 5 + email_clicks * 10), 100)
        phone_score = min(phone_calls * 20, 100)
        demo_score = 100 if demo_attended else 0
        website_score = min((pages_viewed * 2 + time_on_site_minutes * 0.5), 100)

        # Weighted sum
        lead_score = (
            engagement * weights["engagement"]
            + email_score * weights["email"]
            + phone_score * weights["phone"]
            + demo_score * weights["demo"]
            + website_score * weights["website"]
        )

        # Confidence (0-1) based on data richness
        data_points = sum([1 for x in [email_opens, phone_calls, website_visits] if x > 0])
        confidence = min(0.5 + (data_points * 0.15), 1.0)

        # Tier classification
        if lead_score >= 75:
            tier = "hot"
        elif lead_score >= 50:
            tier = "warm"
        else:
            tier = "cold"

        # Top factors
        factors = []
        if email_score > 50:
            factors.append("high_email_engagement")
        if demo_attended:
            factors.append("demo_attended")
        if phone_calls > 0:
            factors.append("engaged_by_phone")
        if website_visits > 5:
            factors.append("active_website_user")

        # Save or update
        result = await db.execute(
            select(LeadScoringModel).where(
                (LeadScoringModel.business_id == business_id)
                & (LeadScoringModel.lead_id == customer_id)
            )
        )
        lead_model = result.scalar()

        if lead_model:
            lead_model.lead_score = lead_score
            lead_model.confidence = confidence
            lead_model.tier = tier
            lead_model.top_factors = factors
            lead_model.engagement_score = engagement_score
            lead_model.email_opens = email_opens
            lead_model.email_clicks = email_clicks
            lead_model.phone_calls = phone_calls
            lead_model.demo_attended = demo_attended
            lead_model.website_visits = website_visits
            lead_model.pages_viewed = pages_viewed
            lead_model.time_on_site_minutes = time_on_site_minutes
        else:
            lead_model = LeadScoringModel(
                business_id=business_id,
                lead_id=customer_id,
                lead_score=lead_score,
                confidence=confidence,
                tier=tier,
                top_factors=factors,
                engagement_score=engagement_score,
                email_opens=email_opens,
                email_clicks=email_clicks,
                phone_calls=phone_calls,
                demo_attended=demo_attended,
                website_visits=website_visits,
                pages_viewed=pages_viewed,
                time_on_site_minutes=time_on_site_minutes,
            )
            db.add(lead_model)

        await db.commit()
        await db.refresh(lead_model)
        return lead_model

    @staticmethod
    async def predict_churn(
        db: AsyncSession,
        business_id: UUID,
        customer_id: UUID,
        days_since_last_purchase: int,
        total_lifetime_value: float,
        purchase_frequency_per_month: float,
        support_tickets: int,
        nps_score: Optional[int] = None,
    ) -> ChurnPredictionModel:
        """Predict churn probability."""
        # Churn risk factors (simplified)
        churn_probability = 0.0

        # Factor: recency (days since last purchase)
        if days_since_last_purchase > 180:
            churn_probability += 0.4
        elif days_since_last_purchase > 90:
            churn_probability += 0.2
        elif days_since_last_purchase > 30:
            churn_probability += 0.05

        # Factor: frequency (purchase frequency)
        if purchase_frequency_per_month < 0.5:
            churn_probability += 0.3
        elif purchase_frequency_per_month < 1:
            churn_probability += 0.1

        # Factor: NPS (Net Promoter Score)
        if nps_score is not None:
            if nps_score < 30:
                churn_probability += 0.3
            elif nps_score < 50:
                churn_probability += 0.1

        # Factor: support tickets (high = higher churn risk)
        if support_tickets > 5:
            churn_probability += 0.2

        # Cap at 1.0
        churn_probability = min(churn_probability, 1.0)

        # Risk classification
        if churn_probability >= 0.7:
            churn_risk = "high"
            days_until_churn = 14
            recommended_action = "special_offer"
        elif churn_probability >= 0.4:
            churn_risk = "medium"
            days_until_churn = 30
            recommended_action = "loyalty_program"
        else:
            churn_risk = "low"
            days_until_churn = None
            recommended_action = "maintain_engagement"

        # Save or update
        result = await db.execute(
            select(ChurnPredictionModel).where(
                (ChurnPredictionModel.business_id == business_id)
                & (ChurnPredictionModel.customer_id == customer_id)
            )
        )
        churn_model = result.scalar()

        if churn_model:
            churn_model.churn_probability = churn_probability
            churn_model.churn_risk = churn_risk
            churn_model.days_until_churn = days_until_churn
            churn_model.recommended_action = recommended_action
            churn_model.days_since_last_purchase = days_since_last_purchase
            churn_model.purchase_frequency_per_month = purchase_frequency_per_month
            churn_model.total_lifetime_value = total_lifetime_value
            churn_model.support_tickets = support_tickets
            churn_model.nps_score = nps_score
        else:
            churn_model = ChurnPredictionModel(
                business_id=business_id,
                customer_id=customer_id,
                churn_probability=churn_probability,
                churn_risk=churn_risk,
                days_until_churn=days_until_churn,
                recommended_action=recommended_action,
                days_since_last_purchase=days_since_last_purchase,
                purchase_frequency_per_month=purchase_frequency_per_month,
                total_lifetime_value=total_lifetime_value,
                support_tickets=support_tickets,
                nps_score=nps_score,
            )
            db.add(churn_model)

        await db.commit()
        await db.refresh(churn_model)
        return churn_model

    @staticmethod
    async def calculate_clv(
        db: AsyncSession,
        business_id: UUID,
        customer_id: UUID,
        total_spent: float,
        total_orders: int,
        customer_lifespan_days: int,
    ) -> CLVModel:
        """Calculate Customer Lifetime Value."""
        avg_order_value = total_spent / total_orders if total_orders > 0 else 0
        purchase_frequency = total_orders / (customer_lifespan_days / 30) if customer_lifespan_days > 0 else 0
        repeat_rate = min((total_orders - 1) / total_orders if total_orders > 1 else 0, 1.0)

        # CLV formula: AOV × Purchase Frequency × Customer Lifespan (36 months)
        predicted_clv_12m = avg_order_value * purchase_frequency * 12
        predicted_clv_36m = avg_order_value * purchase_frequency * 36

        # Segment
        if predicted_clv_36m > 10000:
            clv_segment = "vip"
            upsell_propensity = 0.8
            crosssell_propensity = 0.7
        elif predicted_clv_36m > 1000:
            clv_segment = "standard"
            upsell_propensity = 0.5
            crosssell_propensity = 0.4
        else:
            clv_segment = "at_risk"
            upsell_propensity = 0.2
            crosssell_propensity = 0.1

        expansion_propensity = min(repeat_rate * 0.8, 1.0)

        # Save or update
        result = await db.execute(
            select(CLVModel).where(
                (CLVModel.business_id == business_id) & (CLVModel.customer_id == customer_id)
            )
        )
        clv_model = result.scalar()

        if clv_model:
            clv_model.predicted_clv_12m = predicted_clv_12m
            clv_model.predicted_clv_36m = predicted_clv_36m
            clv_model.clv_segment = clv_segment
            clv_model.upsell_propensity = upsell_propensity
            clv_model.crosssell_propensity = crosssell_propensity
            clv_model.expansion_propensity = expansion_propensity
        else:
            clv_model = CLVModel(
                business_id=business_id,
                customer_id=customer_id,
                total_spent=total_spent,
                total_orders=total_orders,
                avg_order_value=avg_order_value,
                purchase_frequency_days=365 / purchase_frequency if purchase_frequency > 0 else 0,
                customer_lifespan_days=customer_lifespan_days,
                repeat_rate=repeat_rate,
                predicted_clv_12m=predicted_clv_12m,
                predicted_clv_36m=predicted_clv_36m,
                clv_segment=clv_segment,
                upsell_propensity=upsell_propensity,
                crosssell_propensity=crosssell_propensity,
                expansion_propensity=expansion_propensity,
            )
            db.add(clv_model)

        await db.commit()
        await db.refresh(clv_model)
        return clv_model
