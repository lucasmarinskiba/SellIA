"""Journey orchestration service."""

import logging
from datetime import datetime, timezone
from uuid import UUID
from typing import List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.domains.journeys.journey_models import (
    CustomerJourney, JourneyVariant, JourneyExecution, JourneyMetrics, ABTestResult
)

logger = logging.getLogger(__name__)


class JourneyService:
    """Customer journey orchestration."""

    @staticmethod
    def create_journey(business_id: UUID, name: str, nodes: Dict, edges: Dict, db: Session = None) -> dict:
        if not db:
            raise ValueError("Database session required")
        
        journey = CustomerJourney(business_id=business_id, name=name, nodes=nodes, edges=edges)
        db.add(journey)
        db.commit()
        logger.info(f"Journey created: {journey.id}")
        return {"journey_id": str(journey.id), "name": name}

    @staticmethod
    def create_variant(journey_id: UUID, business_id: UUID, variant_name: str, config: Dict, traffic_allocation: float = 50.0, db: Session = None) -> dict:
        if not db:
            raise ValueError("Database session required")
        
        variant = JourneyVariant(journey_id=journey_id, business_id=business_id, variant_name=variant_name, variant_config=config, traffic_allocation=traffic_allocation)
        db.add(variant)
        db.commit()
        logger.info(f"Variant created: {variant.id}")
        return {"variant_id": str(variant.id), "variant_name": variant_name}

    @staticmethod
    def enroll_customer(journey_id: UUID, customer_id: UUID, business_id: UUID, variant_id: UUID = None, db: Session = None) -> dict:
        if not db:
            raise ValueError("Database session required")
        
        execution = JourneyExecution(journey_id=journey_id, business_id=business_id, customer_id=customer_id, variant_id=variant_id, status="active")
        db.add(execution)
        db.commit()
        logger.info(f"Customer enrolled: {customer_id} in journey {journey_id}")
        return {"execution_id": str(execution.id), "status": "active"}

    @staticmethod
    def get_journey_executions(journey_id: UUID, limit: int = 50, db: Session = None) -> List[dict]:
        if not db:
            raise ValueError("Database session required")
        
        executions = db.query(JourneyExecution).filter(JourneyExecution.journey_id == journey_id).order_by(desc(JourneyExecution.started_at)).limit(limit).all()
        return [{"execution_id": str(e.id), "customer_id": str(e.customer_id), "status": e.status} for e in executions]

    @staticmethod
    def get_ab_test_result(journey_id: UUID, variant_a_id: UUID, variant_b_id: UUID, db: Session = None) -> dict:
        if not db:
            raise ValueError("Database session required")
        
        result = db.query(ABTestResult).filter(ABTestResult.journey_id == journey_id).first()
        if not result:
            return {"message": "No test result found"}
        
        return {"variant_a_value": result.variant_a_value, "variant_b_value": result.variant_b_value, "winner": result.winner}

    @staticmethod
    def get_metrics(business_id: UUID, db: Session = None) -> dict:
        if not db:
            raise ValueError("Database session required")
        
        metrics = db.query(JourneyMetrics).filter(JourneyMetrics.business_id == business_id).first()
        if not metrics:
            return {"message": "No metrics found"}
        return {"total_journeys": metrics.total_journeys, "completion_rate": metrics.completion_rate}
