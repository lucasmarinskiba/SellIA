"""Test memory endpoint - ultra minimal"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/test")
async def test_endpoint():
    """Minimal test endpoint"""
    return {"status": "ok", "message": "memory router test endpoint"}


@router.get("/me")
async def get_memory():
    """Minimal memory endpoint"""
    return {
        "user_id": "test",
        "status": "ok",
        "engagement_score": 0.5,
        "total_messages": 0,
    }
