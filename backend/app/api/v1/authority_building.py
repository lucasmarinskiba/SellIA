"""Phase 3 Authority Building endpoints - E-E-A-T signals, testimonials, awards."""

from fastapi import APIRouter, HTTPException, Query, Depends, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta

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
    """E-E-A-T trust score computed from this seller's REAL rows.

    This used to be five random.uniform()/randint() calls dressed up as a
    score: every reload invented a different "82.5 GOLD · 234 reviews ·
    8 years" for any seller id, including ones that do not exist. It now
    reads platform_reviews/testimonials/awards, and when a seller has no
    rows at all it says so (available: false) instead of manufacturing a
    plausible number.
    """
    reviews_result = await db.execute(
        select(Review).where(Review.seller_id == seller_id, Review.is_flagged == False)  # noqa: E712
    )
    reviews = reviews_result.scalars().all()

    testimonials_result = await db.execute(
        select(Testimonial).where(Testimonial.seller_id == seller_id)
    )
    testimonials = testimonials_result.scalars().all()

    awards_result = await db.execute(select(Award).where(Award.seller_id == seller_id))
    awards = awards_result.scalars().all()

    if not reviews and not testimonials and not awards:
        return {
            "seller_id": seller_id,
            "available": False,
            "reason": (
                "Todavía no hay reseñas, testimonios ni premios cargados para esta "
                "cuenta. El score aparece cuando existan señales reales."
            ),
            "components": {
                "review_count": 0,
                "testimonial_count": 0,
                "award_count": 0,
            },
        }

    review_count = len(reviews)
    review_rating = round(sum(r.rating for r in reviews) / review_count, 2) if review_count else 0.0
    answered = sum(1 for r in reviews if r.seller_response)
    response_rate = round(answered / review_count * 100, 1) if review_count else 0.0
    verified_reviews = sum(1 for r in reviews if r.is_verified_purchase)
    verification = round(verified_reviews / review_count * 100, 1) if review_count else 0.0

    # Each component is a real measurement, weighted into 0-100. No component
    # is included unless the data behind it exists.
    trust_score = round(
        review_rating * 10           # max 50 (5 stars)
        + min(review_count / 2, 20)  # max 20
        + response_rate * 0.15       # max 15
        + verification * 0.10        # max 10
        + min(len(awards) * 2.5, 5),  # max 5
        1,
    )

    if trust_score >= 90:
        tier = "platinum"
    elif trust_score >= 75:
        tier = "gold"
    elif trust_score >= 60:
        tier = "silver"
    else:
        tier = "bronze"

    thresholds = {"bronze": 60, "silver": 75, "gold": 90, "platinum": 100}
    return {
        "seller_id": seller_id,
        "available": True,
        "trust_score": trust_score,
        "tier": tier,
        "components": {
            "review_rating": review_rating,
            "review_count": review_count,
            "responded_reviews": answered,
            "response_rate": response_rate,
            "verified_purchase_rate": verification,
            "testimonial_count": len(testimonials),
            "award_count": len(awards),
        },
        "next_tier": None if tier == "platinum" else (
            "silver" if tier == "bronze" else "gold" if tier == "silver" else "platinum"
        ),
        "points_to_next": max(0, round(thresholds.get(tier, 100) - trust_score, 1)),
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
        # "your_rating"/"your_reviews" used to be random numbers presented as
        # this seller's own benchmark, and the category averages were invented
        # constants. Real per-seller figures come from GET /authority/reviews/
        # {seller_id} and /authority/trust-score/{seller_id}, both counted from
        # actual platform_reviews rows.
        "benchmarks": {
            "available": False,
            "reason": (
                "No hay datos de benchmark de categoría cargados. Tus números reales "
                "están en /authority/reviews/{seller_id} y /authority/trust-score/{seller_id}."
            ),
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
