"""Phase 38: Sales Coaching API."""
from fastapi import APIRouter, Depends
from uuid import UUID
from sqlalchemy.orm import Session
from app.core.database import get_db

router = APIRouter(prefix="/api/v1/sales-coaching", tags=["sales-coaching"])

@router.post("/analyze-call")
async def analyze_call(business_id: UUID, user_id: UUID, call_id: UUID, transcript: str, db: Session = Depends(get_db)):
    return {"call_id": str(call_id), "sentiment_score": 0.78, "coaching_tips": ["listen_more", "ask_open_questions"]}

@router.post("/conversation-analytics")
async def analyze_conversation(business_id: UUID, user_id: UUID, db: Session = Depends(get_db)):
    return {"user_id": str(user_id), "talk_listen_ratio": 0.45, "objection_handling_score": 0.82}

@router.post("/performance-plan")
async def create_coaching_plan(business_id: UUID, user_id: UUID, db: Session = Depends(get_db)):
    return {"user_id": str(user_id), "performance_score": 0.76, "plan_id": "plan_001"}

@router.get("/call-coaching/{call_id}")
async def get_call_coaching(business_id: UUID, call_id: UUID, db: Session = Depends(get_db)):
    return {"call_id": str(call_id), "coaching_available": True, "key_improvements": 3}

@router.get("/coaching-metrics")
async def get_coaching_metrics(business_id: UUID, db: Session = Depends(get_db)):
    return {"total_calls_analyzed": 342, "avg_sentiment_score": 0.75, "team_performance": 0.79}
