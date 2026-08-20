"""API management — rate limiting, caching, metrics."""

from uuid import UUID
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.domains.api_management.rate_limit_service import RateLimitService

router = APIRouter(prefix="/api/v1", tags=["api-management"])


class CreateApiKeyRequest(BaseModel):
    key_name: str
    tier: str = "starter"  # free, starter, pro, enterprise
    custom_limit: Optional[int] = None
    expires_at: Optional[str] = None  # ISO datetime


class SetCachePolicyRequest(BaseModel):
    endpoint_path: str
    ttl_seconds: int = 300
    cache_by: Optional[str] = None  # user_id, business_id, etc


@router.post("/businesses/{business_id}/api-keys")
def create_api_key(
    business_id: UUID,
    request: CreateApiKeyRequest,
    db: Session = Depends(get_db)
):
    """Create new API key."""
    expires = None
    if request.expires_at:
        expires = datetime.fromisoformat(request.expires_at)

    return RateLimitService.create_api_key(
        business_id=business_id,
        key_name=request.key_name,
        tier=request.tier,
        custom_limit=request.custom_limit,
        expires_at=expires,
        db=db
    )


@router.get("/api-keys/{api_key_id}/rate-limit-status")
def get_rate_limit_status(
    api_key_id: UUID,
    db: Session = Depends(get_db)
):
    """Get current rate limit status."""
    return RateLimitService.get_rate_limit_status(
        api_key_id=api_key_id,
        db=db
    )


@router.post("/businesses/{business_id}/cache-policy")
def set_cache_policy(
    business_id: UUID,
    request: SetCachePolicyRequest,
    db: Session = Depends(get_db)
):
    """Set cache policy for endpoint."""
    return RateLimitService.set_cache_policy(
        business_id=business_id,
        endpoint_path=request.endpoint_path,
        ttl_seconds=request.ttl_seconds,
        cache_by=request.cache_by,
        db=db
    )


@router.get("/businesses/{business_id}/api-metrics")
def get_api_metrics(
    business_id: UUID,
    date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    """Get API performance metrics."""
    return RateLimitService.get_api_metrics(
        business_id=business_id,
        date=date,
        db=db
    )
