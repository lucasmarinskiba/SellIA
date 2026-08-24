"""Memory endpoints - Phase 29"""

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import decode_access_token
from app.domains.user_memory.service import UserMemoryService
from app.domains.user_memory.schemas import UserMemoryResponse, UserMemoryUpdate

router = APIRouter()


async def get_user_id(authorization: str = Header(None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")
    token = authorization[7:]
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload["sub"]


@router.get("/me")
async def get_memory(user_id: str = Depends(get_user_id), db: AsyncSession = Depends(get_db)):
    """Get user memory"""
    try:
        service = UserMemoryService(db)
        memory = await service.get_or_create(user_id)
        return UserMemoryResponse(
            id=str(memory.id),
            user_id=str(memory.user_id),
            preferred_language=memory.preferred_language,
            preferred_tone=memory.preferred_tone,
            industry_focus=memory.industry_focus,
            business_stage=memory.business_stage,
            primary_business_type=memory.primary_business_type,
            target_audience_summary=memory.target_audience_summary,
            key_challenges=memory.key_challenges or [],
            key_interests=memory.key_interests or [],
            technologies_used=memory.technologies_used or [],
            total_conversations=memory.total_conversations,
            total_messages=memory.total_messages,
            favorite_agents=memory.favorite_agents or [],
            frequently_asked_topics=memory.frequently_asked_topics or [],
            engagement_score=memory.engagement_score,
            satisfaction_score=memory.satisfaction_score,
            churn_risk_score=memory.churn_risk_score,
            lifetime_value_estimate=memory.lifetime_value_estimate,
            last_active_business_id=str(memory.last_active_business_id) if memory.last_active_business_id else None,
            last_active_conversation_id=str(memory.last_active_conversation_id) if memory.last_active_conversation_id else None,
            last_active_agent_id=str(memory.last_active_agent_id) if memory.last_active_agent_id else None,
            created_at=memory.created_at,
            updated_at=memory.updated_at,
            last_activity_at=memory.last_activity_at,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/me")
async def update_memory(data: dict, user_id: str = Depends(get_user_id), db: AsyncSession = Depends(get_db)):
    """Update user memory"""
    try:
        service = UserMemoryService(db)
        update_data = UserMemoryUpdate(**data)
        memory = await service.update_memory(user_id, update_data)
        return {"status": "updated", "user_id": str(memory.user_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/events")
async def log_event(data: dict, user_id: str = Depends(get_user_id), db: AsyncSession = Depends(get_db)):
    """Log event"""
    try:
        service = UserMemoryService(db)
        memory = await service.log_event(user_id, data)
        return {"status": "logged", "total_messages": memory.total_messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/interests/{interest}")
async def add_interest(interest: str, user_id: str = Depends(get_user_id), db: AsyncSession = Depends(get_db)):
    """Add interest"""
    try:
        service = UserMemoryService(db)
        memory = await service.add_interest(user_id, interest)
        return {"status": "added", "interests": memory.key_interests}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/challenges/{challenge}")
async def add_challenge(challenge: str, user_id: str = Depends(get_user_id), db: AsyncSession = Depends(get_db)):
    """Add challenge"""
    try:
        service = UserMemoryService(db)
        memory = await service.add_challenge(user_id, challenge)
        return {"status": "added", "challenges": memory.key_challenges}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/preferences")
async def set_preference(data: dict, user_id: str = Depends(get_user_id), db: AsyncSession = Depends(get_db)):
    """Set preference"""
    try:
        service = UserMemoryService(db)
        pref = await service.set_preference(user_id, data.get("key"), data.get("value"))
        return {"status": "set", "key": data.get("key")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/preferences/{key}")
async def get_preference(key: str, user_id: str = Depends(get_user_id), db: AsyncSession = Depends(get_db)):
    """Get preference"""
    try:
        service = UserMemoryService(db)
        value = await service.get_preference(user_id, key)
        return {"key": key, "value": value}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events")
async def get_events(limit: int = 50, user_id: str = Depends(get_user_id), db: AsyncSession = Depends(get_db)):
    """Get recent events"""
    try:
        service = UserMemoryService(db)
        events = await service.get_recent_events(user_id, limit)
        return {"events": events, "count": len(events)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
