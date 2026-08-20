"""Customer segmentation service — RFM + behavioral + churn prediction."""

import logging
from datetime import datetime, timezone, timedelta
from uuid import UUID
from typing import Optional, Dict, Tuple
from decimal import Decimal
from statistics import stdev, mean

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.domains.segmentation.segmentation_models import (
    CustomerSegment, SegmentationMetrics, SegmentationStrategy,
    RFMSegment, BehavioralSegment, ChurnRiskLevel
)

logger = logging.getLogger(__name__)


class SegmentationService:
    """Calculate customer segments and RFM scores."""

    @staticmethod
    def calculate_rfm_scores(
        business_id: UUID,
        days_window: int = 365,
        db: Session = None
    ) -> dict:
        """Calculate RFM segments for all customers."""
        if not db:
            raise ValueError("Database session required")

        from app.domains.customers.models import Customer
        from app.domains.orders.models import Order

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_window)

        customers = db.query(Customer).filter(
            Customer.business_id == business_id
        ).all()

        if not customers:
            return {"segmentation_calculated": False}

        # Calculate RFM for each customer
        rfm_data = []
        for customer in customers:
            orders = db.query(Order).filter(
                Order.customer_id == customer.id,
                Order.created_at >= cutoff_date
            ).all()

            if not orders:
                continue

            # Recency: days since last order
            last_order_date = max(o.created_at for o in orders)
            recency_days = (datetime.now(timezone.utc) - last_order_date).days

            # Frequency: order count
            frequency = len(orders)

            # Monetary: total spend
            monetary = sum(float(o.total_value) for o in orders if o.total_value)

            rfm_data.append({
                "customer_id": customer.id,
                "recency": recency_days,
                "frequency": frequency,
                "monetary": Decimal(str(monetary))
            })

        if not rfm_data:
            return {"segmentation_calculated": False}

        # Score each dimension (0-5 scale)
        recency_values = [r["recency"] for r in rfm_data]
        frequency_values = [r["frequency"] for r in rfm_data]
        monetary_values = [float(r["monetary"]) for r in rfm_data]

        recency_quartiles = SegmentationService._quartiles(recency_values)
        frequency_quartiles = SegmentationService._quartiles(frequency_values)
        monetary_quartiles = SegmentationService._quartiles(monetary_values)

        updated_count = 0
        for data in rfm_data:
            # Lower recency is better (more recent)
            r_score = 5 if data["recency"] <= recency_quartiles[0] else \
                     4 if data["recency"] <= recency_quartiles[1] else \
                     3 if data["recency"] <= recency_quartiles[2] else \
                     2 if data["recency"] <= recency_quartiles[3] else 1

            # Higher frequency is better
            f_score = 5 if data["frequency"] >= frequency_quartiles[3] else \
                     4 if data["frequency"] >= frequency_quartiles[2] else \
                     3 if data["frequency"] >= frequency_quartiles[1] else \
                     2 if data["frequency"] >= frequency_quartiles[0] else 1

            # Higher monetary is better
            m_score = 5 if data["monetary"] >= monetary_quartiles[3] else \
                     4 if data["monetary"] >= monetary_quartiles[2] else \
                     3 if data["monetary"] >= monetary_quartiles[1] else \
                     2 if data["monetary"] >= monetary_quartiles[0] else 1

            composite = (r_score + f_score + m_score) // 3

            # Determine segment
            if composite >= 4:
                segment = RFMSegment.CHAMPIONS
            elif composite == 3:
                if r_score >= 4:
                    segment = RFMSegment.POTENTIAL_LOYALISTS
                else:
                    segment = RFMSegment.LOYAL_CUSTOMERS
            elif m_score >= 4:
                segment = RFMSegment.CANT_LOSE_THEM
            elif r_score <= 2:
                segment = RFMSegment.AT_RISK
            else:
                segment = RFMSegment.NEED_ACTIVATION

            # Update or create segment
            seg = db.query(CustomerSegment).filter(
                CustomerSegment.customer_id == data["customer_id"]
            ).first()

            if seg:
                seg.recency_score = r_score
                seg.frequency_score = f_score
                seg.monetary_score = m_score
                seg.rfm_composite = composite
                seg.rfm_segment = segment
                seg.segment_updated_at = datetime.now(timezone.utc)
            else:
                seg = CustomerSegment(
                    business_id=business_id,
                    customer_id=data["customer_id"],
                    recency_score=r_score,
                    frequency_score=f_score,
                    monetary_score=m_score,
                    rfm_composite=composite,
                    rfm_segment=segment
                )
                db.add(seg)

            updated_count += 1
            db.commit()

        logger.info(f"RFM segmentation calculated: {business_id} - {updated_count} customers")

        return {
            "rfm_calculated": True,
            "customers_segmented": updated_count,
            "days_window": days_window
        }

    @staticmethod
    def _quartiles(values: list) -> tuple:
        """Get quartile boundaries (Q1, Q2, Q3)."""
        if not values:
            return (0, 0, 0, 0)
        sorted_vals = sorted(values)
        n = len(sorted_vals)
        q1 = sorted_vals[n // 4] if n > 0 else 0
        q2 = sorted_vals[n // 2] if n > 0 else 0
        q3 = sorted_vals[3 * n // 4] if n > 0 else 0
        return (q1, q2, q3, max(sorted_vals))

    @staticmethod
    def calculate_churn_risk(
        business_id: UUID,
        db: Session = None
    ) -> dict:
        """Predict churn risk for customers."""
        if not db:
            raise ValueError("Database session required")

        from app.domains.customers.models import Customer
        from app.domains.orders.models import Order

        segments = db.query(CustomerSegment).filter(
            CustomerSegment.business_id == business_id
        ).all()

        if not segments:
            return {"churn_calculated": False}

        updated_count = 0
        for seg in segments:
            customer = db.query(Customer).filter(Customer.id == seg.customer_id).first()
            if not customer:
                continue

            # Get purchase history
            orders = db.query(Order).filter(
                Order.customer_id == seg.customer_id
            ).order_by(Order.created_at).all()

            if not orders:
                seg.churn_probability = Decimal("90")  # No purchase history = high risk
                seg.churn_risk_level = ChurnRiskLevel.CRITICAL
                db.commit()
                updated_count += 1
                continue

            # Days since last purchase
            last_purchase = max(o.created_at for o in orders)
            days_since = (datetime.now(timezone.utc) - last_purchase).days
            seg.days_since_purchase = days_since

            # Purchase interval consistency (std dev)
            if len(orders) > 2:
                intervals = []
                for i in range(1, len(orders)):
                    interval = (orders[i].created_at - orders[i-1].created_at).days
                    intervals.append(interval)
                consistency = stdev(intervals) if len(intervals) > 1 else 0
                seg.purchase_consistency_score = Decimal(str(min(10, consistency / 10)))
            else:
                seg.purchase_consistency_score = Decimal("5")

            # Churn probability (simple model)
            base_churn = 0
            if days_since > 180:
                base_churn += 40
            elif days_since > 90:
                base_churn += 20
            elif days_since > 30:
                base_churn += 5

            # Frequency factor
            if seg.frequency_score <= 1:
                base_churn += 40
            elif seg.frequency_score <= 2:
                base_churn += 25
            elif seg.frequency_score >= 5:
                base_churn -= 30

            # Monetary factor (high-value customers less likely to churn)
            if seg.monetary_score >= 4:
                base_churn -= 20
            elif seg.monetary_score <= 1:
                base_churn += 15

            churn_prob = max(0, min(100, base_churn))
            seg.churn_probability = Decimal(str(churn_prob))

            if churn_prob >= 81:
                seg.churn_risk_level = ChurnRiskLevel.CRITICAL
            elif churn_prob >= 51:
                seg.churn_risk_level = ChurnRiskLevel.HIGH
            elif churn_prob >= 11:
                seg.churn_risk_level = ChurnRiskLevel.MEDIUM
            else:
                seg.churn_risk_level = ChurnRiskLevel.LOW

            db.commit()
            updated_count += 1

        logger.info(f"Churn risk calculated: {business_id} - {updated_count} customers")

        return {
            "churn_calculated": True,
            "customers_assessed": updated_count
        }

    @staticmethod
    def calculate_clv_scores(
        business_id: UUID,
        db: Session = None
    ) -> dict:
        """Calculate Customer Lifetime Value scores."""
        if not db:
            raise ValueError("Database session required")

        from app.domains.customers.models import Customer

        segments = db.query(CustomerSegment).filter(
            CustomerSegment.business_id == business_id
        ).all()

        if not segments:
            return {"clv_calculated": False}

        clv_values = []
        for seg in segments:
            # CLV = (avg_order_value * purchase_frequency * customer_lifespan_years)
            # Simplified: CLV = monetary_score * frequency_score * (1 - churn_prob/100)

            monetary_weight = float(seg.monetary_score or 1) / 5
            frequency_weight = float(seg.frequency_score or 1) / 5
            churn_factor = 1 - (float(seg.churn_probability or 0) / 100)

            clv = Decimal(str(round(1000 * monetary_weight * frequency_weight * churn_factor, 2)))
            seg.clv_score = clv
            clv_values.append(float(clv))
            db.commit()

        # Calculate percentiles
        if clv_values:
            sorted_clv = sorted(clv_values)
            for seg in segments:
                percentile = (sorted_clv.index(float(seg.clv_score)) / len(sorted_clv)) * 100
                seg.clv_percentile = int(percentile)
                db.commit()

        logger.info(f"CLV scores calculated: {business_id} - {len(segments)} customers")

        return {
            "clv_calculated": True,
            "customers_scored": len(segments)
        }

    @staticmethod
    def get_segment_summary(
        business_id: UUID,
        date: str = None,
        db: Session = None
    ) -> dict:
        """Get segmentation summary."""
        if not db:
            raise ValueError("Database session required")

        if not date:
            date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        segments = db.query(CustomerSegment).filter(
            CustomerSegment.business_id == business_id
        ).all()

        if not segments:
            return {"summary_available": False}

        # Count by RFM segment
        rfm_counts = {}
        for seg in segments:
            if seg.rfm_segment:
                key = seg.rfm_segment.value
                rfm_counts[key] = rfm_counts.get(key, 0) + 1

        # Count by behavioral segment
        behavioral_counts = {}
        for seg in segments:
            if seg.behavioral_segment:
                key = seg.behavioral_segment.value
                behavioral_counts[key] = behavioral_counts.get(key, 0) + 1

        # Count by churn risk
        churn_counts = {}
        for seg in segments:
            key = seg.churn_risk_level.value
            churn_counts[key] = churn_counts.get(key, 0) + 1

        avg_clv = sum(float(s.clv_score) for s in segments) / len(segments) if segments else 0
        avg_engagement = sum(float(s.overall_engagement_score or 0) for s in segments) / len(segments) if segments else 0

        # Create metrics record
        metrics = SegmentationMetrics(
            business_id=business_id,
            date=date,
            champions_count=rfm_counts.get("champions", 0),
            loyal_customers_count=rfm_counts.get("loyal_customers", 0),
            potential_loyalists_count=rfm_counts.get("potential_loyalists", 0),
            at_risk_count=rfm_counts.get("at_risk", 0),
            cant_lose_them_count=rfm_counts.get("cant_lose_them", 0),
            need_activation_count=rfm_counts.get("need_activation", 0),
            low_risk=churn_counts.get("low", 0),
            medium_risk=churn_counts.get("medium", 0),
            high_risk=churn_counts.get("high", 0),
            critical_risk=churn_counts.get("critical", 0),
            avg_clv=Decimal(str(round(avg_clv, 2))),
            avg_engagement_score=Decimal(str(round(avg_engagement, 1))),
            churn_risk_count=churn_counts.get("high", 0) + churn_counts.get("critical", 0)
        )

        db.add(metrics)
        db.commit()

        logger.info(f"Segment summary generated: {business_id} - {date}")

        return {
            "summary_generated": True,
            "date": date,
            "total_customers": len(segments),
            "rfm_distribution": rfm_counts,
            "behavioral_distribution": behavioral_counts,
            "churn_distribution": churn_counts,
            "avg_clv": float(avg_clv),
            "avg_engagement": float(avg_engagement)
        }
