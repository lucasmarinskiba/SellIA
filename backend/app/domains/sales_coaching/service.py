"""Sales Coaching service."""
from uuid import UUID
from sqlalchemy.orm import Session

class SalesCoachingService:
    @staticmethod
    def analyze_call(business_id: UUID, call_id: UUID, transcript: str, db: Session = None) -> dict:
        return {"call_id": str(call_id), "sentiment": 0.78, "tips": ["listen_more"]}

    @staticmethod
    def conversation_analytics(business_id: UUID, user_id: UUID, db: Session = None) -> dict:
        return {"user_id": str(user_id), "talk_listen_ratio": 0.45}

    @staticmethod
    def coaching_plan(business_id: UUID, user_id: UUID, db: Session = None) -> dict:
        return {"user_id": str(user_id), "performance_score": 0.76}
