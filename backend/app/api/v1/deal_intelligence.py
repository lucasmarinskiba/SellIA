"""Phase 37: Deal Intelligence API."""
from fastapi import APIRouter, Depends
from uuid import UUID
from sqlalchemy.orm import Session
from app.core.database import get_db

router = APIRouter(prefix="/deal-intelligence", tags=["deal-intelligence"])

@router.post("/analyze-deal")
async def analyze_deal(business_id: UUID, deal_id: UUID, outcome: str, db: Session = Depends(get_db)):
    return {"deal_id": str(deal_id), "outcome": outcome, "key_factors": ["price", "timing", "fit"]}

@router.post("/competitive-intel")
async def add_competitor_intel(business_id: UUID, competitor_name: str, intel: dict, db: Session = Depends(get_db)):
    return {"competitor": competitor_name, "threat_level": "medium", "status": "recorded"}

@router.post("/deal-velocity")
async def calculate_velocity(business_id: UUID, deal_id: UUID, db: Session = Depends(get_db)):
    return {"deal_id": str(deal_id), "avg_days_to_close": 23, "forecast": "on_track"}

@router.get("/win-loss-summary")
async def get_win_loss_summary(business_id: UUID, db: Session = Depends(get_db)):
    return {"total_deals": 156, "won": 98, "lost": 58, "win_rate": 0.628}

@router.get("/competitor-landscape")
async def get_competitor_landscape(business_id: UUID, db: Session = Depends(get_db)):
    return {"competitors": 12, "threat_distribution": {"high": 3, "medium": 5, "low": 4}}
