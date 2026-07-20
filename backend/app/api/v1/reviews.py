"""
Reviews & Testimonials — Sistema de reseñas, moderation, spam detection.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, List, Any
from datetime import datetime
import logging
import re

router = APIRouter(prefix="/api/v1/reviews", tags=["reviews"])
logger = logging.getLogger(__name__)

# Mock reviews DB
_REVIEWS_DB: Dict[str, Any] = {}
_REVIEW_COUNTER = 0


class Review(BaseModel):
    """Reseña de producto."""
    id: str
    product_id: str
    customer_id: str
    customer_name: str
    rating: int  # 1-5
    text: str
    verified_purchase: bool
    status: str  # pending, approved, spam
    created_at: datetime


@router.post("/products/{product_id}/reviews", tags=["create"])
async def create_review(
    product_id: str,
    customer_id: str,
    customer_name: str,
    rating: int,
    text: str,
    verified_purchase: bool = True,
):
    """
    Crear reseña de producto.

    AI detecta spam automáticamente.
    """

    global _REVIEW_COUNTER

    try:
        # Validar rating
        if not (1 <= rating <= 5):
            raise HTTPException(status_code=400, detail="Rating must be 1-5")

        # Validar texto (min 10 caracteres)
        if len(text) < 10:
            raise HTTPException(status_code=400, detail="Review too short (min 10 chars)")

        # Detectar spam
        spam_patterns = [
            r"(?i)(viagra|cialis|casino|pharma|forex)",
            r"(?i)(click.*here|buy.*now|limited.*offer)",
            r"(?i)(fake|scam|don't.*buy)",
        ]

        is_spam = any(re.search(pattern, text) for pattern in spam_patterns)

        # Contar palabras repetidas (posible bot)
        words = text.lower().split()
        unique_words = len(set(words))
        if len(words) > 20 and unique_words < len(words) * 0.5:  # <50% unique = spam
            is_spam = True

        review_id = f"rev_{_REVIEW_COUNTER}"
        _REVIEW_COUNTER += 1

        review = {
            "id": review_id,
            "product_id": product_id,
            "customer_id": customer_id,
            "customer_name": customer_name,
            "rating": rating,
            "text": text,
            "verified_purchase": verified_purchase,
            "status": "spam" if is_spam else "pending",  # Pending = espera moderación
            "created_at": datetime.utcnow().isoformat(),
        }

        _REVIEWS_DB[review_id] = review

        status_msg = "pending_moderation" if review["status"] == "pending" else "flagged_as_spam"
        logger.info(f"Reseña creada: {review_id} (⭐{rating}), status: {status_msg}")

        return {
            "status": "submitted",
            "review_id": review_id,
            "moderation": status_msg,
        }

    except Exception as e:
        logger.error(f"Error creando reseña: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/products/{product_id}/reviews", tags=["list"])
async def get_product_reviews(product_id: str, approved_only: bool = True):
    """
    Obtener reseñas de producto.

    Calcula promedio rating.
    """

    reviews = [r for r in _REVIEWS_DB.values() if r["product_id"] == product_id]

    if approved_only:
        reviews = [r for r in reviews if r["status"] == "approved"]

    # Calcular promedio
    if reviews:
        avg_rating = sum(r["rating"] for r in reviews) / len(reviews)
    else:
        avg_rating = 0.0

    return {
        "product_id": product_id,
        "total_reviews": len(reviews),
        "average_rating": round(avg_rating, 1),
        "reviews": reviews,
    }


@router.post("/reviews/{review_id}/approve", tags=["moderation"])
async def approve_review(review_id: str):
    """Admin: aprobar reseña."""

    if review_id not in _REVIEWS_DB:
        raise HTTPException(status_code=404, detail="Review not found")

    review = _REVIEWS_DB[review_id]
    review["status"] = "approved"

    logger.info(f"Reseña aprobada: {review_id} (⭐{review['rating']})")

    return {"status": "approved", "review_id": review_id}


@router.post("/reviews/{review_id}/reject", tags=["moderation"])
async def reject_review(review_id: str, reason: str = "spam"):
    """Admin: rechazar reseña."""

    if review_id not in _REVIEWS_DB:
        raise HTTPException(status_code=404, detail="Review not found")

    review = _REVIEWS_DB[review_id]
    review["status"] = "rejected"

    logger.info(f"Reseña rechazada: {review_id}, razón: {reason}")

    return {"status": "rejected", "review_id": review_id, "reason": reason}


@router.get("/reviews/pending", tags=["moderation"])
async def get_pending_reviews():
    """Admin: reseñas pendientes de moderación."""

    pending = [r for r in _REVIEWS_DB.values() if r["status"] == "pending"]

    return {"total": len(pending), "reviews": pending}
