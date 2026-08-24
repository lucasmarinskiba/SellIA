"""Memory endpoints - Phase 29 - Deferred imports"""

from fastapi import APIRouter, Depends, Header, HTTPException
from datetime import datetime
import json

router = APIRouter()


async def get_user_id(authorization: str = Header(None)) -> str:
    """Extract user_id from Bearer token"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")
    token = authorization[7:]

    from app.core.security import decode_access_token
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload["sub"]


async def get_db():
    """Get database session"""
    from app.core.database import get_db as _get_db
    async for session in _get_db():
        yield session


@router.get("/me")
async def get_memory(user_id: str = Depends(get_user_id), db = Depends(get_db)):
    """Get user memory"""
    try:
        from sqlalchemy import text
        result = await db.execute(
            text("SELECT * FROM user_memory WHERE user_id = :uid"),
            {"uid": user_id}
        )
        row = result.fetchone()
        if not row:
            # Auto-create
            await db.execute(
                text("""INSERT INTO user_memory
                (user_id, preferred_language, preferred_tone, industry_focus, business_stage,
                 primary_business_type, target_audience_summary, key_challenges, key_interests,
                 technologies_used, total_conversations, total_messages, favorite_agents,
                 frequently_asked_topics, engagement_score, satisfaction_score, churn_risk_score,
                 lifetime_value_estimate, last_activity_at, created_at, updated_at)
                VALUES (:uid, 'en', 'professional', NULL, NULL, NULL, NULL, '[]', '[]', '[]',
                0, 0, '[]', '[]', 0.0, 0.0, 0.0, 0.0, NOW(), NOW(), NOW())"""),
                {"uid": user_id}
            )
            await db.commit()
            result = await db.execute(
                text("SELECT * FROM user_memory WHERE user_id = :uid"),
                {"uid": user_id}
            )
            row = result.fetchone()

        return {
            "id": str(row[0]) if row[0] else None,
            "user_id": row[1],
            "preferred_language": row[2],
            "preferred_tone": row[3],
            "industry_focus": row[4],
            "business_stage": row[5],
            "primary_business_type": row[6],
            "target_audience_summary": row[7],
            "key_challenges": json.loads(row[8]) if row[8] else [],
            "key_interests": json.loads(row[9]) if row[9] else [],
            "technologies_used": json.loads(row[10]) if row[10] else [],
            "total_conversations": row[11],
            "total_messages": row[12],
            "favorite_agents": json.loads(row[13]) if row[13] else [],
            "frequently_asked_topics": json.loads(row[14]) if row[14] else [],
            "engagement_score": row[15],
            "satisfaction_score": row[16],
            "churn_risk_score": row[17],
            "lifetime_value_estimate": row[18],
            "created_at": row[19],
            "updated_at": row[20],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/me")
async def update_memory(data: dict, user_id: str = Depends(get_user_id), db = Depends(get_db)):
    """Update user memory"""
    try:
        from sqlalchemy import text
        set_clause = []
        params = {"uid": user_id}
        for i, (key, value) in enumerate(data.items()):
            if key in ["key_challenges", "key_interests", "technologies_used", "favorite_agents", "frequently_asked_topics"]:
                val = json.dumps(value) if isinstance(value, list) else value
            else:
                val = value
            param_name = f"val{i}"
            set_clause.append(f"{key} = :{param_name}")
            params[param_name] = val

        set_clause.append("updated_at = NOW()")
        sql = f"UPDATE user_memory SET {', '.join(set_clause)} WHERE user_id = :uid"

        await db.execute(text(sql), params)
        await db.commit()
        return {"status": "updated", "user_id": user_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/events")
async def log_event(data: dict, user_id: str = Depends(get_user_id), db = Depends(get_db)):
    """Log event"""
    try:
        from sqlalchemy import text
        event_type = data.get("event_type", "action")
        event_data = data.get("data", {})

        await db.execute(
            text("""INSERT INTO user_memory_events
            (user_id, event_type, event_data, created_at)
            VALUES (:uid, :et, :ed, NOW())"""),
            {"uid": user_id, "et": event_type, "ed": json.dumps(event_data)}
        )

        # Increment total_messages in user_memory
        await db.execute(
            text("UPDATE user_memory SET total_messages = total_messages + 1 WHERE user_id = :uid"),
            {"uid": user_id}
        )

        await db.commit()

        result = await db.execute(
            text("SELECT total_messages FROM user_memory WHERE user_id = :uid"),
            {"uid": user_id}
        )
        row = result.fetchone()

        return {"status": "logged", "total_messages": row[0] if row else 0}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/interests/{interest}")
async def add_interest(interest: str, user_id: str = Depends(get_user_id), db = Depends(get_db)):
    """Add interest"""
    try:
        from sqlalchemy import text
        result = await db.execute(
            text("SELECT key_interests FROM user_memory WHERE user_id = :uid"),
            {"uid": user_id}
        )
        row = result.fetchone()
        interests = json.loads(row[0]) if row and row[0] else []

        if interest not in interests:
            interests.append(interest)

        await db.execute(
            text("UPDATE user_memory SET key_interests = :interests WHERE user_id = :uid"),
            {"uid": user_id, "interests": json.dumps(interests)}
        )
        await db.commit()

        return {"status": "added", "interests": interests}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/challenges/{challenge}")
async def add_challenge(challenge: str, user_id: str = Depends(get_user_id), db = Depends(get_db)):
    """Add challenge"""
    try:
        from sqlalchemy import text
        result = await db.execute(
            text("SELECT key_challenges FROM user_memory WHERE user_id = :uid"),
            {"uid": user_id}
        )
        row = result.fetchone()
        challenges = json.loads(row[0]) if row and row[0] else []

        if challenge not in challenges:
            challenges.append(challenge)

        await db.execute(
            text("UPDATE user_memory SET key_challenges = :challenges WHERE user_id = :uid"),
            {"uid": user_id, "challenges": json.dumps(challenges)}
        )
        await db.commit()

        return {"status": "added", "challenges": challenges}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/preferences")
async def set_preference(data: dict, user_id: str = Depends(get_user_id), db = Depends(get_db)):
    """Set preference"""
    try:
        from sqlalchemy import text
        key = data.get("key")
        value = data.get("value")

        # Try update first
        result = await db.execute(
            text("UPDATE user_preferences SET preference_value = :val WHERE user_id = :uid AND preference_key = :key"),
            {"uid": user_id, "key": key, "val": json.dumps(value)}
        )

        # If no rows updated, insert
        if result.rowcount == 0:
            await db.execute(
                text("""INSERT INTO user_preferences (user_id, preference_key, preference_value, created_at, updated_at)
                VALUES (:uid, :key, :val, NOW(), NOW())"""),
                {"uid": user_id, "key": key, "val": json.dumps(value)}
            )

        await db.commit()
        return {"status": "set", "key": key}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/preferences/{key}")
async def get_preference(key: str, user_id: str = Depends(get_user_id), db = Depends(get_db)):
    """Get preference"""
    try:
        from sqlalchemy import text
        result = await db.execute(
            text("SELECT preference_value FROM user_preferences WHERE user_id = :uid AND preference_key = :key"),
            {"uid": user_id, "key": key}
        )
        row = result.fetchone()
        value = json.loads(row[0]) if row and row[0] else None
        return {"key": key, "value": value}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events")
async def get_events(limit: int = 50, user_id: str = Depends(get_user_id), db = Depends(get_db)):
    """Get recent events"""
    try:
        from sqlalchemy import text
        result = await db.execute(
            text("""SELECT id, event_type, event_data, created_at FROM user_memory_events
            WHERE user_id = :uid ORDER BY created_at DESC LIMIT :limit"""),
            {"uid": user_id, "limit": limit}
        )
        rows = result.fetchall()
        events = [
            {
                "id": str(row[0]),
                "event_type": row[1],
                "event_data": json.loads(row[2]) if row[2] else {},
                "created_at": row[3]
            }
            for row in rows
        ]
        return {"events": events, "count": len(events)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
