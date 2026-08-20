"""Customer 360 & unified data platform service."""

import logging
from datetime import datetime, timezone, timedelta
from uuid import UUID
from typing import Optional, Dict, List

from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.domains.customer_360.customer_360_models import (
    CustomerProfile, CustomerScores, CustomerSegmentMembership, CustomerInsights,
    Customer360Metadata, LifecycleStage
)

logger = logging.getLogger(__name__)


class Customer360Service:
    """Unified customer 360 view & data platform."""

    @staticmethod
    def get_customer_360_profile(
        customer_id: UUID,
        business_id: UUID,
        db: Session = None
    ) -> dict:
        """Get complete 360 customer profile."""
        if not db:
            raise ValueError("Database session required")

        # Get profile
        profile = db.query(CustomerProfile).filter(
            CustomerProfile.customer_id == customer_id,
            CustomerProfile.business_id == business_id
        ).first()

        if not profile:
            return {"message": "Customer not found"}

        # Get scores
        scores = db.query(CustomerScores).filter(
            CustomerScores.customer_id == customer_id
        ).first()

        # Get segments
        segments = db.query(CustomerSegmentMembership).filter(
            CustomerSegmentMembership.customer_id == customer_id,
            CustomerSegmentMembership.is_active == True
        ).all()

        # Get insights
        insights = db.query(CustomerInsights).filter(
            CustomerInsights.customer_id == customer_id,
            CustomerInsights.is_actioned == False,
            CustomerInsights.is_dismissed == False
        ).order_by(desc(CustomerInsights.confidence_score)).limit(10).all()

        # Get metadata
        metadata = db.query(Customer360Metadata).filter(
            Customer360Metadata.customer_id == customer_id
        ).first()

        return {
            "profile": {
                "id": str(profile.id),
                "first_name": profile.first_name,
                "last_name": profile.last_name,
                "email": profile.email,
                "phone": profile.phone,
                "company": profile.company,
                "industry": profile.industry,
                "lifecycle_stage": profile.lifecycle_stage,
                "tags": profile.tags,
                "source": profile.source,
            },
            "scores": {
                "rfm_total": scores.rfm_total_score if scores else 0,
                "customer_lifetime_value": scores.customer_lifetime_value if scores else 0,
                "churn_risk": scores.churn_risk_score if scores else 0,
                "propensity_to_buy": scores.propensity_to_buy_score if scores else 0,
                "engagement": scores.engagement_score if scores else 0,
                "health": scores.health_score if scores else 0,
                "next_best_action": scores.next_best_action if scores else None,
                "next_best_channel": scores.next_best_channel if scores else None,
            },
            "segments": [
                {
                    "name": s.segment_name,
                    "type": s.segment_type,
                    "score": s.segment_score,
                }
                for s in segments
            ],
            "insights": [
                {
                    "insight_id": str(i.id),
                    "type": i.insight_type,
                    "title": i.title,
                    "description": i.description,
                    "confidence": i.confidence_score,
                    "recommended_action": i.recommended_action,
                    "recommended_channel": i.recommended_channel,
                }
                for i in insights
            ],
            "metadata": {
                "profile_completeness": metadata.profile_completeness_pct if metadata else 0,
                "data_sources": metadata.data_sources_count if metadata else 0,
                "data_quality": metadata.data_quality_score if metadata else 0,
                "last_computed": metadata.last_360_computed_at.isoformat() if metadata and metadata.last_360_computed_at else None,
            }
        }

    @staticmethod
    def calculate_customer_scores(
        customer_id: UUID,
        business_id: UUID,
        db: Session = None
    ) -> dict:
        """Calculate/update all customer scores."""
        if not db:
            raise ValueError("Database session required")

        scores = db.query(CustomerScores).filter(
            CustomerScores.customer_id == customer_id
        ).first()

        if not scores:
            scores = CustomerScores(
                business_id=business_id,
                customer_id=customer_id
            )
            db.add(scores)

        # Calculate RFM (placeholder - in production would aggregate from orders/interactions)
        scores.recency_score = Customer360Service._calculate_recency(customer_id, db)
        scores.frequency_score = Customer360Service._calculate_frequency(customer_id, db)
        scores.monetary_score = Customer360Service._calculate_monetary(customer_id, db)
        scores.rfm_total_score = round((scores.recency_score + scores.frequency_score + scores.monetary_score) / 3)

        # CLV
        scores.customer_lifetime_value = Customer360Service._calculate_clv(customer_id, db)

        # Predictive scores
        scores.churn_risk_score = Customer360Service._calculate_churn_risk(customer_id, db)
        scores.propensity_to_buy_score = Customer360Service._calculate_propensity(customer_id, db)
        scores.engagement_score = Customer360Service._calculate_engagement(customer_id, db)

        # Health score
        scores.health_score = round((scores.rfm_total_score + scores.engagement_score) / 2)

        # Next best action
        scores.next_best_action, scores.next_best_channel = Customer360Service._calculate_nba(customer_id, scores, db)

        scores.scores_calculated_at = datetime.now(timezone.utc)
        db.commit()

        logger.info(f"Scores calculated for customer {customer_id}")

        return {
            "customer_id": str(customer_id),
            "rfm_score": scores.rfm_total_score,
            "clv": scores.customer_lifetime_value,
            "churn_risk": scores.churn_risk_score,
            "engagement": scores.engagement_score,
            "health": scores.health_score,
        }

    @staticmethod
    def _calculate_recency(customer_id: UUID, db: Session) -> int:
        """Calculate recency score (0-100)."""
        # Placeholder: in production would check last interaction
        return 75

    @staticmethod
    def _calculate_frequency(customer_id: UUID, db: Session) -> int:
        """Calculate frequency score (0-100)."""
        # Placeholder: in production would count interactions
        return 60

    @staticmethod
    def _calculate_monetary(customer_id: UUID, db: Session) -> int:
        """Calculate monetary score (0-100)."""
        # Placeholder: in production would sum revenue
        return 80

    @staticmethod
    def _calculate_clv(customer_id: UUID, db: Session) -> int:
        """Calculate customer lifetime value."""
        # Placeholder
        return 5000

    @staticmethod
    def _calculate_churn_risk(customer_id: UUID, db: Session) -> int:
        """Calculate churn risk (0-100, 100=high risk)."""
        # Placeholder: in production would use ML model
        return 25

    @staticmethod
    def _calculate_propensity(customer_id: UUID, db: Session) -> int:
        """Calculate propensity to buy (0-100)."""
        # Placeholder
        return 65

    @staticmethod
    def _calculate_engagement(customer_id: UUID, db: Session) -> int:
        """Calculate engagement score (0-100)."""
        # Placeholder
        return 70

    @staticmethod
    def _calculate_nba(customer_id: UUID, scores: CustomerScores, db: Session) -> tuple:
        """Calculate next best action."""
        # Logic: if high propensity, recommend email; if high churn risk, recommend retention email
        if scores.churn_risk_score > 70:
            return ("Re-engagement email", "email")
        elif scores.propensity_to_buy_score > 70:
            return ("Product recommendation", "email")
        elif scores.engagement_score < 40:
            return ("Survey request", "sms")
        else:
            return ("Check-in call", "call")

    @staticmethod
    def get_customer_scores(
        customer_id: UUID,
        db: Session = None
    ) -> dict:
        """Get customer scores."""
        if not db:
            raise ValueError("Database session required")

        scores = db.query(CustomerScores).filter(
            CustomerScores.customer_id == customer_id
        ).first()

        if not scores:
            return {"message": "No scores found"}

        return {
            "rfm_score": scores.rfm_total_score,
            "recency": scores.recency_score,
            "frequency": scores.frequency_score,
            "monetary": scores.monetary_score,
            "customer_lifetime_value": scores.customer_lifetime_value,
            "lifetime_purchases": scores.lifetime_purchases,
            "churn_risk": scores.churn_risk_score,
            "propensity_to_buy": scores.propensity_to_buy_score,
            "engagement": scores.engagement_score,
            "health": scores.health_score,
            "next_best_action": scores.next_best_action,
            "next_best_channel": scores.next_best_channel,
        }

    @staticmethod
    def get_customer_insights(
        customer_id: UUID,
        limit: int = 10,
        db: Session = None
    ) -> List[dict]:
        """Get customer insights."""
        if not db:
            raise ValueError("Database session required")

        insights = db.query(CustomerInsights).filter(
            CustomerInsights.customer_id == customer_id,
            CustomerInsights.is_dismissed == False
        ).order_by(desc(CustomerInsights.confidence_score)).limit(limit).all()

        return [
            {
                "insight_id": str(i.id),
                "type": i.insight_type,
                "title": i.title,
                "description": i.description,
                "confidence": i.confidence_score,
                "recommended_action": i.recommended_action,
                "recommended_channel": i.recommended_channel,
                "estimated_impact": i.estimated_impact,
            }
            for i in insights
        ]

    @staticmethod
    def get_segment_customers(
        business_id: UUID,
        segment_name: str,
        limit: int = 100,
        db: Session = None
    ) -> List[dict]:
        """Get all customers in segment."""
        if not db:
            raise ValueError("Database session required")

        memberships = db.query(CustomerSegmentMembership).filter(
            CustomerSegmentMembership.business_id == business_id,
            CustomerSegmentMembership.segment_name == segment_name,
            CustomerSegmentMembership.is_active == True
        ).limit(limit).all()

        return [
            {
                "customer_id": str(m.customer_id),
                "segment": m.segment_name,
                "joined_at": m.joined_at.isoformat(),
                "segment_score": m.segment_score,
            }
            for m in memberships
        ]

    @staticmethod
    def search_customers(
        business_id: UUID,
        query: str,
        limit: int = 50,
        db: Session = None
    ) -> List[dict]:
        """Search customers by name/email/company."""
        if not db:
            raise ValueError("Database session required")

        results = db.query(CustomerProfile).filter(
            CustomerProfile.business_id == business_id,
            (CustomerProfile.first_name.ilike(f"%{query}%")) |
            (CustomerProfile.last_name.ilike(f"%{query}%")) |
            (CustomerProfile.email.ilike(f"%{query}%")) |
            (CustomerProfile.company.ilike(f"%{query}%"))
        ).limit(limit).all()

        return [
            {
                "customer_id": str(p.customer_id),
                "name": f"{p.first_name} {p.last_name}".strip(),
                "email": p.email,
                "company": p.company,
                "lifecycle_stage": p.lifecycle_stage,
            }
            for p in results
        ]

    @staticmethod
    def dismiss_insight(
        insight_id: UUID,
        db: Session = None
    ) -> dict:
        """Dismiss an insight."""
        if not db:
            raise ValueError("Database session required")

        insight = db.query(CustomerInsights).filter(
            CustomerInsights.id == insight_id
        ).first()

        if not insight:
            raise ValueError("Insight not found")

        insight.is_dismissed = True
        db.commit()

        return {"insight_id": str(insight_id), "dismissed": True}

    @staticmethod
    def mark_insight_actioned(
        insight_id: UUID,
        db: Session = None
    ) -> dict:
        """Mark insight as actioned."""
        if not db:
            raise ValueError("Database session required")

        insight = db.query(CustomerInsights).filter(
            CustomerInsights.id == insight_id
        ).first()

        if not insight:
            raise ValueError("Insight not found")

        insight.is_actioned = True
        insight.actioned_at = datetime.now(timezone.utc)
        db.commit()

        return {"insight_id": str(insight_id), "actioned": True}
