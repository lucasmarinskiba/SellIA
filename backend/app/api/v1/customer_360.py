"""Customer 360 API endpoints."""

from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.domains.customer_360.customer_360_service import Customer360Service

router = APIRouter(prefix="/api/v1", tags=["customer-360"])


@router.get("/customers/{customer_id}/profile")
def get_customer_360_profile(
    customer_id: UUID,
    business_id: UUID = Query(...),
    db: Session = Depends(get_db)
):
    """Get complete 360 customer profile."""
    return Customer360Service.get_customer_360_profile(
        customer_id=customer_id,
        business_id=business_id,
        db=db
    )


@router.get("/customers/{customer_id}/scores")
def get_customer_scores(
    customer_id: UUID,
    db: Session = Depends(get_db)
):
    """Get customer scores."""
    return Customer360Service.get_customer_scores(
        customer_id=customer_id,
        db=db
    )


@router.post("/customers/{customer_id}/scores/calculate")
def calculate_customer_scores(
    customer_id: UUID,
    business_id: UUID = Query(...),
    db: Session = Depends(get_db)
):
    """Calculate/update customer scores."""
    return Customer360Service.calculate_customer_scores(
        customer_id=customer_id,
        business_id=business_id,
        db=db
    )


@router.get("/customers/{customer_id}/insights")
def get_customer_insights(
    customer_id: UUID,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get customer insights."""
    return Customer360Service.get_customer_insights(
        customer_id=customer_id,
        limit=limit,
        db=db
    )


@router.post("/insights/{insight_id}/dismiss")
def dismiss_insight(
    insight_id: UUID,
    db: Session = Depends(get_db)
):
    """Dismiss insight."""
    return Customer360Service.dismiss_insight(
        insight_id=insight_id,
        db=db
    )


@router.post("/insights/{insight_id}/action")
def mark_insight_actioned(
    insight_id: UUID,
    db: Session = Depends(get_db)
):
    """Mark insight as actioned."""
    return Customer360Service.mark_insight_actioned(
        insight_id=insight_id,
        db=db
    )


@router.get("/customers/segment/{segment_id}")
def get_segment_customers(
    segment_id: str = Path(...),
    business_id: UUID = Query(...),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get all customers in segment."""
    return Customer360Service.get_segment_customers(
        business_id=business_id,
        segment_name=segment_id,
        limit=limit,
        db=db
    )


@router.get("/customers/search")
def search_customers(
    business_id: UUID = Query(...),
    query: str = Query(..., min_length=2),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Search customers."""
    return Customer360Service.search_customers(
        business_id=business_id,
        query=query,
        limit=limit,
        db=db
    )
