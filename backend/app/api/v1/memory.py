"""Memory endpoints - Phase 29 - Deferred imports

JSONB columns are handled with explicit casts rather than relying on
driver-level auto (de)serialization, which proved inconsistent between
raw asyncpg and SQLAlchemy's asyncpg dialect in this environment:
  - write: json.dumps(value) bound as a plain string, cast to ::jsonb in SQL
  - read:  column selected with ::text, then json.loads() client-side
This is deterministic regardless of what codec (if any) the connection
has registered.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
import json
import uuid

router = APIRouter()


def _loads(value):
    """Defensively parse a jsonb::text value. Returns the raw value if
    it's not a JSON string (e.g. driver already decoded it)."""
    if value is None:
        return None
    if isinstance(value, str):
        try:
            return json.loads(value)
        except ValueError:
            return value
    return value


async def get_user_id(request: Request) -> str:
    """Extract user_id from either the Authorization: Bearer header or the
    httpOnly access_token cookie — the dashboard's real login flow only
    sets the cookie (JS can't read it to build a Bearer header), so both
    must be supported. Reuses the same token-extraction path as the rest
    of the app (app.core.deps.get_token_from_request) rather than only
    checking the header, which silently 401s every cookie-authenticated
    request from the dashboard."""
    from app.core.deps import get_token_from_request
    from app.core.security import decode_access_token

    token = await get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")

    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload["sub"]


async def get_db():
    """Get database session"""
    from app.core.database import get_db as _get_db
    async for session in _get_db():
        yield session


MEMORY_COLUMNS = """id, user_id, preferred_language, preferred_tone, industry_focus, business_stage,
                 primary_business_type, target_audience_summary,
                 key_challenges::text, key_interests::text, technologies_used::text,
                 total_conversations, total_messages,
                 favorite_agents::text, frequently_asked_topics::text,
                 engagement_score, satisfaction_score, churn_risk_score,
                 lifetime_value_estimate, created_at, updated_at"""


async def _ensure_memory_row(user_id: str, db) -> None:
    """Idempotently create the user_memory row if it doesn't exist yet.
    Every endpoint that reads/writes user_memory must call this first —
    only GET /me used to do this, so calling any other endpoint (PATCH,
    events, interests, challenges) before ever calling GET /me silently
    no-op'd against a nonexistent row."""
    from sqlalchemy import text
    await db.execute(
        text("""INSERT INTO user_memory
        (id, user_id, preferred_language, preferred_tone, industry_focus, business_stage,
         primary_business_type, target_audience_summary, key_challenges, key_interests,
         technologies_used, total_conversations, total_messages, favorite_agents,
         frequently_asked_topics, engagement_score, satisfaction_score, churn_risk_score,
         lifetime_value_estimate, last_activity_at, created_at, updated_at)
        VALUES (:new_id, :uid, 'en', 'professional', NULL, NULL, NULL, NULL,
        '[]'::jsonb, '[]'::jsonb, '[]'::jsonb,
        0, 0, '[]'::jsonb, '[]'::jsonb, 0.0, 0.0, 0.0, 'low', NOW(), NOW(), NOW())
        ON CONFLICT (user_id) DO NOTHING"""),
        {"uid": user_id, "new_id": str(uuid.uuid4())}
    )
    await db.commit()


@router.get("/me")
async def get_memory(user_id: str = Depends(get_user_id), db = Depends(get_db)):
    """Get user memory"""
    try:
        from sqlalchemy import text
        await _ensure_memory_row(user_id, db)
        result = await db.execute(
            text(f"SELECT {MEMORY_COLUMNS} FROM user_memory WHERE user_id = :uid"),
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
            "key_challenges": _loads(row[8]) or [],
            "key_interests": _loads(row[9]) or [],
            "technologies_used": _loads(row[10]) or [],
            "total_conversations": row[11],
            "total_messages": row[12],
            "favorite_agents": _loads(row[13]) or [],
            "frequently_asked_topics": _loads(row[14]) or [],
            "engagement_score": row[15],
            "satisfaction_score": row[16],
            "churn_risk_score": row[17],
            "lifetime_value_estimate": row[18],
            "created_at": row[19],
            "updated_at": row[20],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


JSONB_MEMORY_FIELDS = {"key_challenges", "key_interests", "technologies_used", "favorite_agents", "frequently_asked_topics"}


@router.patch("/me")
async def update_memory(data: dict, user_id: str = Depends(get_user_id), db = Depends(get_db)):
    """Update user memory"""
    try:
        from sqlalchemy import text
        await _ensure_memory_row(user_id, db)
        set_clause = []
        params = {"uid": user_id}
        for i, (key, value) in enumerate(data.items()):
            param_name = f"val{i}"
            if key in JSONB_MEMORY_FIELDS:
                set_clause.append(f"{key} = CAST(:{param_name} AS jsonb)")
                params[param_name] = json.dumps(value)
            else:
                set_clause.append(f"{key} = :{param_name}")
                params[param_name] = value

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
        await _ensure_memory_row(user_id, db)
        event_type = data.get("event_type", "action")
        event_data = data.get("data", {})

        await db.execute(
            text("""INSERT INTO user_memory_events
            (id, user_id, event_type, event_data, created_at)
            VALUES (:new_id, :uid, :et, CAST(:ed AS jsonb), NOW())"""),
            {"new_id": str(uuid.uuid4()), "uid": user_id, "et": event_type, "ed": json.dumps(event_data)}
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
        await _ensure_memory_row(user_id, db)
        result = await db.execute(
            text("SELECT key_interests::text FROM user_memory WHERE user_id = :uid"),
            {"uid": user_id}
        )
        row = result.fetchone()
        interests = (_loads(row[0]) if row else None) or []

        if interest not in interests:
            interests.append(interest)

        await db.execute(
            text("UPDATE user_memory SET key_interests = CAST(:interests AS jsonb) WHERE user_id = :uid"),
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
        await _ensure_memory_row(user_id, db)
        result = await db.execute(
            text("SELECT key_challenges::text FROM user_memory WHERE user_id = :uid"),
            {"uid": user_id}
        )
        row = result.fetchone()
        challenges = (_loads(row[0]) if row else None) or []

        if challenge not in challenges:
            challenges.append(challenge)

        await db.execute(
            text("UPDATE user_memory SET key_challenges = CAST(:challenges AS jsonb) WHERE user_id = :uid"),
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
        val_json = json.dumps(value)

        # Try update first
        result = await db.execute(
            text("UPDATE user_preferences SET preference_value = CAST(:val AS jsonb) WHERE user_id = :uid AND preference_key = :key"),
            {"uid": user_id, "key": key, "val": val_json}
        )

        # If no rows updated, insert
        if result.rowcount == 0:
            await db.execute(
                text("""INSERT INTO user_preferences (id, user_id, preference_key, preference_value, created_at, updated_at)
                VALUES (:new_id, :uid, :key, CAST(:val AS jsonb), NOW(), NOW())"""),
                {"new_id": str(uuid.uuid4()), "uid": user_id, "key": key, "val": val_json}
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
            text("SELECT preference_value::text FROM user_preferences WHERE user_id = :uid AND preference_key = :key"),
            {"uid": user_id, "key": key}
        )
        row = result.fetchone()
        value = _loads(row[0]) if row else None
        return {"key": key, "value": value}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events")
async def get_events(limit: int = 50, user_id: str = Depends(get_user_id), db = Depends(get_db)):
    """Get recent events"""
    try:
        from sqlalchemy import text
        result = await db.execute(
            text("""SELECT id, event_type, event_data::text, created_at FROM user_memory_events
            WHERE user_id = :uid ORDER BY created_at DESC LIMIT :limit"""),
            {"uid": user_id, "limit": limit}
        )
        rows = result.fetchall()
        events = [
            {
                "id": str(row[0]),
                "event_type": row[1],
                "event_data": _loads(row[2]) or {},
                "created_at": row[3]
            }
            for row in rows
        ]
        return {"events": events, "count": len(events)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
