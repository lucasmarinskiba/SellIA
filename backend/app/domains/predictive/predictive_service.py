"""Predictive modeling service."""

import logging
from datetime import datetime, timezone
from uuid import UUID
from typing import Optional, Dict, List
import math

from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.domains.predictive.predictive_models import (
    CustomerScore, DynamicSegment, SegmentMembership, LookalikeAudience,
    PredictionLog, PredictiveMetrics
)

logger = logging.getLogger(__name__)


class PredictiveService:
    """ML predictive modeling."""

    @staticmethod
    def calculate_lead_score(customer_id: UUID, business_id: UUID, rfm: float, engagement: float, frequency: float, db: Session = None) -> dict:
        if not db:
            raise ValueError("Database session required")
        
        lead_score = (rfm * 0.3 + engagement * 0.3 + min(frequency * 10, 100) * 0.4)
        lead_score = min(max(lead_score, 0), 100)
        
        score = db.query(CustomerScore).filter(CustomerScore.customer_id == customer_id).first()
        if not score:
            score = CustomerScore(customer_id=customer_id, business_id=business_id)
            db.add(score)
        
        score.lead_score = lead_score
        db.commit()
        return {"customer_id": str(customer_id), "lead_score": lead_score}

    @staticmethod
    def calculate_churn_risk(customer_id: UUID, business_id: UUID, days_since_purchase: int, engagement: float, frequency: float, db: Session = None) -> dict:
        if not db:
            raise ValueError("Database session required")
        
        decay = 100 * (1 - math.exp(-days_since_purchase * 0.03))
        churn_risk = decay * (1 - engagement / 100 * 0.3) * (1 - min(frequency / 10, 1) * 0.2)
        churn_risk = min(max(churn_risk, 0), 100)
        
        score = db.query(CustomerScore).filter(CustomerScore.customer_id == customer_id).first()
        if not score:
            score = CustomerScore(customer_id=customer_id, business_id=business_id)
            db.add(score)
        
        score.churn_risk = churn_risk
        db.commit()
        return {"customer_id": str(customer_id), "churn_risk": churn_risk}

    @staticmethod
    def create_segment(business_id: UUID, name: str, rules: Dict, seg_type: str, db: Session = None) -> dict:
        if not db:
            raise ValueError("Database session required")
        
        segment = DynamicSegment(business_id=business_id, name=name, rules=rules, segmentation_type=seg_type)
        db.add(segment)
        db.commit()
        return {"segment_id": str(segment.id), "name": name}

    @staticmethod
    def get_metrics(business_id: UUID, db: Session = None) -> dict:
        if not db:
            raise ValueError("Database session required")
        
        metrics = db.query(PredictiveMetrics).filter(PredictiveMetrics.business_id == business_id).first()
        return {"avg_lead_score": metrics.avg_lead_score if metrics else 0}
