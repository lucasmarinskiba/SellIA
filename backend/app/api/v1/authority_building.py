"""Phase 3 Authority Building endpoints - E-E-A-T signals, testimonials, awards."""

from fastapi import APIRouter, HTTPException, Query, Depends, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
import random

from app.core.database import get_db
from app.models.authority_building import (
    Testimonial, Award, Review, TrustScore, SellerBio
)

router = APIRouter(prefix="/authority", tags=["authority"])


@router.post("/testimonials")
async def create_testimonial(
    seller_id: str = Query(...),
    customer_name: str = Body(...),
    title: str = Body(...),
    content: str = Body(...),
    db: AsyncSession = Depends(get_db),
):
    """Add customer testimonial (manual or from video)."""
    testimonial = Testimonial(
        seller_id=seller_id,
        customer_name=customer_name,
        title=title,
        content=content,
        rating=5,
        is_verified=False,
    )
    db.add(testimonial)
    await db.commit()
    await db.refresh(testimonial)
    return testimonial


@router.get("/testimonials/{seller_id}")
async def list_testimonials(
    seller_id: str,
    featured_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    """List testimonials for seller."""
    stmt = select(Testimonial).where(Testimonial.seller_id == seller_id)
    if featured_only:
        stmt = stmt.where(Testimonial.is_featured == True)
    result = await db.execute(stmt)
    testimonials = result.scalars().all()
    return {
        "count": len(testimonials),
        "testimonials": testimonials,
        "avg_rating": sum(t.rating for t in testimonials) / len(testimonials) if testimonials else 0,
    }


@router.post("/awards")
async def add_award(
    seller_id: str = Query(...),
    name: str = Body(...),
    issuer: str = Body(...),
    category: str = Body(...),
    db: AsyncSession = Depends(get_db),
):
    """Register award/certification."""
    award = Award(
        seller_id=seller_id,
        name=name,
        issuer=issuer,
        category=category,
        awarded_date=datetime.utcnow(),
        is_active=True,
    )
    db.add(award)
    await db.commit()
    await db.refresh(award)
    return award


@router.get("/awards/{seller_id}")
async def list_awards(seller_id: str, db: AsyncSession = Depends(get_db)):
    """List active awards for seller."""
    stmt = select(Award).where(
        Award.seller_id == seller_id,
        Award.is_active == True,
    )
    result = await db.execute(stmt)
    awards = result.scalars().all()
    return {
        "count": len(awards),
        "awards": awards,
        "categories": list(set(a.category for a in awards)),
    }


@router.get("/reviews/{seller_id}")
async def get_seller_reviews(
    seller_id: str,
    platform: str = Query(None),
    min_rating: int = Query(1),
    db: AsyncSession = Depends(get_db),
):
    """Aggregated reviews across platforms."""
    stmt = select(Review).where(
        Review.seller_id == seller_id,
        Review.rating >= min_rating,
        Review.is_flagged == False,
    )
    if platform:
        stmt = stmt.where(Review.platform == platform)

    result = await db.execute(stmt)
    reviews = result.scalars().all()

    if reviews:
        avg_rating = sum(r.rating for r in reviews) / len(reviews)
        response_rate = sum(1 for r in reviews if r.seller_response) / len(reviews) * 100
    else:
        avg_rating = 0
        response_rate = 0

    return {
        "total_reviews": len(reviews),
        "avg_rating": avg_rating,
        "response_rate": response_rate,
        "breakdown": {
            "5_star": len([r for r in reviews if r.rating == 5]),
            "4_star": len([r for r in reviews if r.rating == 4]),
            "3_star": len([r for r in reviews if r.rating == 3]),
            "2_star": len([r for r in reviews if r.rating == 2]),
            "1_star": len([r for r in reviews if r.rating == 1]),
        },
        "recent": [r for r in sorted(reviews, key=lambda x: x.review_date, reverse=True)][:5],
    }


@router.get("/trust-score/{seller_id}")
async def calculate_trust_score(seller_id: str, db: AsyncSession = Depends(get_db)):
    """Calculate trust/authority score (E-E-A-T)."""
    # Demo calculation — production: fetch real data from all sources
    review_rating = random.uniform(4.0, 5.0)
    review_count = random.randint(50, 500)
    response_rate = random.uniform(0.8, 1.0) * 100
    verification = random.uniform(60, 100)
    longevity = random.uniform(50, 100)

    # Weighted average (0-100)
    trust_score = (
        review_rating * 20 +  # Max 100 (from 5 stars)
        min(review_count / 5, 20) +  # Max 20
        response_rate / 5 +  # Max 20
        verification / 5 +  # Max 20
        longevity / 5  # Max 20
    )

    # Tier assignment
    if trust_score >= 90:
        tier = "platinum"
    elif trust_score >= 75:
        tier = "gold"
    elif trust_score >= 60:
        tier = "silver"
    else:
        tier = "bronze"

    return {
        "seller_id": seller_id,
        "trust_score": round(trust_score, 1),
        "tier": tier,
        "components": {
            "review_rating": round(review_rating, 1),
            "review_count": review_count,
            "response_rate": round(response_rate, 1),
            "verification": round(verification, 1),
            "longevity_years": round(longevity / 10),
        },
        "next_tier": "platinum" if tier != "platinum" else None,
        "points_to_next": max(0, (
            {"bronze": 60, "silver": 75, "gold": 90, "platinum": 100}.get(tier, 100) - trust_score
        )),
    }


@router.get("/authority-insights/{seller_id}")
async def get_authority_insights(seller_id: str):
    """Authority-building recommendations (E-E-A-T improvement roadmap)."""
    return {
        "seller_id": seller_id,
        "quick_wins": [
            {
                "priority": 1,
                "action": "Respond to all reviews within 24h",
                "impact": "+15% trust score",
                "effort": "15 min/day",
            },
            {
                "priority": 2,
                "action": "Add seller bio + LinkedIn profile",
                "impact": "+10% authority signals",
                "effort": "30 min",
            },
            {
                "priority": 3,
                "action": "Collect 10 video testimonials",
                "impact": "+20% CTR",
                "effort": "2-3 days",
            },
        ],
        "authority_levers": {
            "experiential": "Years in business (longevity score)",
            "expertise": "Seller bio, specialties, certifications",
            "authoritativeness": "Media mentions, LinkedIn, website",
            "trustworthiness": "Reviews, response rate, verified badges",
        },
        "benchmarks": {
            "category_avg_rating": 4.2,
            "category_avg_reviews": 150,
            "your_rating": random.uniform(4.3, 4.9),
            "your_reviews": random.randint(50, 300),
        },
    }


@router.post("/seller-bio/{seller_id}")
async def update_seller_bio(
    seller_id: str,
    full_name: str = Body(...),
    bio: str = Body(...),
    years_in_business: int = Body(...),
    db: AsyncSession = Depends(get_db),
):
    """Create/update seller bio (E-E-A-T: Expertise + Authoritativeness + Trustworthiness)."""
    stmt = select(SellerBio).where(SellerBio.seller_id == seller_id)
    result = await db.execute(stmt)
    seller_bio = result.scalars().first()

    if seller_bio:
        seller_bio.full_name = full_name
        seller_bio.bio = bio
        seller_bio.years_in_business = years_in_business
    else:
        seller_bio = SellerBio(
            seller_id=seller_id,
            full_name=full_name,
            bio=bio,
            years_in_business=years_in_business,
        )
        db.add(seller_bio)

    await db.commit()
    await db.refresh(seller_bio)
    return seller_bio
