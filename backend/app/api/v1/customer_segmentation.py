"""Customer segmentation API — RFM + behavioral + churn prediction."""

from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.domains.segmentation.segmentation_service import SegmentationService

router = APIRouter(prefix="/api/v1", tags=["customer-segmentation"])


@router.post("/businesses/{business_id}/calculate-rfm")
def calculate_rfm_segments(
    business_id: UUID,
    days_window: int = Query(365, ge=30, le=1825),
    db: Session = Depends(get_db)
):
    """Calculate RFM segments for all customers."""
    return SegmentationService.calculate_rfm_scores(
        business_id=business_id,
        days_window=days_window,
        db=db
    )


@router.post("/businesses/{business_id}/calculate-churn-risk")
def calculate_churn_risk(
    business_id: UUID,
    db: Session = Depends(get_db)
):
    """Predict churn risk for customers."""
    return SegmentationService.calculate_churn_risk(
        business_id=business_id,
        db=db
    )


@router.post("/businesses/{business_id}/calculate-clv")
def calculate_clv_scores(
    business_id: UUID,
    db: Session = Depends(get_db)
):
    """Calculate Customer Lifetime Value scores."""
    return SegmentationService.calculate_clv_scores(
        business_id=business_id,
        db=db
    )


@router.get("/businesses/{business_id}/segmentation-summary")
def get_segment_summary(
    business_id: UUID,
    date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    """Get segmentation summary and metrics."""
    return SegmentationService.get_segment_summary(
        business_id=business_id,
        date=date,
        db=db
    )
