import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from typing import Any

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.businesses.models import Business, DEFAULT_CONFIGS
from app.domains.businesses.schemas import BusinessCreate, BusinessUpdate, BusinessResponse
from app.domains.subscriptions.services import track_usage

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
async def health():
    """Health check - no dependencies."""
    return {"status": "ok", "service": "businesses"}




@router.post("/test", tags=["debug"])
async def test_endpoint():
    """Minimal test - no dependencies."""
    return {"status": "ok", "endpoint": "business_create_test"}


@router.get("/debug/conversation-state/{business_id}", tags=["debug"])
async def debug_conversation_state(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Temporary: raw dump of conversations/messages/qualifications for a business."""
    from sqlalchemy import select as sa_select
    from app.domains.channels.models import Conversation, Message
    from app.domains.agents.lead_qualifier.models import LeadQualification

    out = {}
    try:
        conv_res = await db.execute(sa_select(Conversation).where(Conversation.business_id == business_id))
        convs = conv_res.scalars().all()
        out["conversations"] = [{"id": str(c.id), "external_id": c.external_id, "lead_email": c.lead_email} for c in convs]

        msg_out = []
        for c in convs:
            msg_res = await db.execute(sa_select(Message).where(Message.conversation_id == c.id))
            msgs = msg_res.scalars().all()
            msg_out.append({"conversation_id": str(c.id), "count": len(msgs), "contents": [m.content for m in msgs]})
        out["messages"] = msg_out

        qual_res = await db.execute(sa_select(LeadQualification).where(LeadQualification.business_id == business_id))
        quals = qual_res.scalars().all()
        out["qualifications"] = [{"id": str(q.id), "status": q.status, "score": float(q.qualification_score), "bant": q.bant_score} for q in quals]
    except Exception as e:
        out["error"] = str(e)
    return out


@router.post("/debug/llm-test", tags=["debug"])
async def debug_llm_test():
    """Temporary: isolate whether the crash is in imports, LLM call, or DB."""
    steps = []
    try:
        steps.append("start")
        import asyncio
        steps.append("import asyncio ok")
        from app.domains.agents.ai_reply import generate_raw_ai_response
        steps.append("import generate_raw_ai_response ok")
        from app.domains.agents.llm_provider import generate_with_fallback
        steps.append("import generate_with_fallback ok")
        from langchain_core.messages import SystemMessage, HumanMessage
        steps.append("import langchain_core ok")
        from app.core.database import AsyncSessionLocal
        steps.append("import AsyncSessionLocal ok")
        async with AsyncSessionLocal() as db:
            steps.append("db session opened")
            result = await asyncio.wait_for(
                generate_with_fallback(
                    db=db,
                    business_id=UUID(int=0),
                    messages=[SystemMessage(content="Responde solo: OK"), HumanMessage(content="test")],
                    model="gpt-4o-mini",
                    max_tokens=10,
                ),
                timeout=15.0,
            )
            steps.append(f"llm call returned: {result.content if result else None}")
        return {"status": "ok", "steps": steps}
    except asyncio.TimeoutError:
        return {"status": "timeout", "steps": steps}
    except BaseException as e:
        return {"status": "error", "type": type(e).__name__, "error": str(e)[:500], "steps": steps}


@router.post("/debug/qualify/{conversation_id}", tags=["debug"])
async def debug_qualify(
    conversation_id: UUID,
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Temporary: directly call qualify_lead and return the result or raw error."""
    from app.domains.agents.lead_qualifier import service as lq_service
    try:
        result = await lq_service.qualify_lead(db=db, conversation_id=conversation_id, business_id=business_id)
        return {"status": "ok", "result": {k: str(v) for k, v in result.items()}}
    except Exception as e:
        import traceback
        return {"status": "error", "error": str(e), "trace": traceback.format_exc()[-1500:]}


@router.post("/debug/add-type-column", tags=["debug"])
async def debug_add_type_column(db: AsyncSession = Depends(get_db)):
    """Temporary: force-apply the businesses.type schema patch immediately."""
    from sqlalchemy import text
    try:
        await db.execute(text("""
            DO $$ BEGIN
                CREATE TYPE businesstype AS ENUM ('services', 'goods', 'digital', 'mixed');
            EXCEPTION WHEN duplicate_object THEN null;
            END $$;
        """))
        await db.execute(text(
            "ALTER TABLE businesses ADD COLUMN IF NOT EXISTS type businesstype NOT NULL DEFAULT 'services'"
        ))
        await db.commit()
        return {"status": "ok"}
    except Exception as e:
        await db.rollback()
        return {"status": "error", "error": str(e)}


@router.post("/debug/create-table/{table_name}", tags=["debug"])
async def debug_create_table(table_name: str):
    """Temporary: attempt to create one CoreBase table and return the raw error."""
    from app.core.database import Base as CoreBase, engine
    table = CoreBase.metadata.tables.get(table_name)
    if table is None:
        return {"error": f"No table named {table_name} in CoreBase.metadata", "available": list(CoreBase.metadata.tables.keys())[:20]}
    try:
        async with engine.begin() as conn:
            await conn.run_sync(lambda sync_conn: table.create(sync_conn, checkfirst=True))
        return {"status": "ok", "table": table_name}
    except Exception as e:
        return {"status": "error", "table": table_name, "error": str(e)}


@router.post("/")
async def create_business(
    business_in: BusinessCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create business - minimal."""
    business = Business(
        user_id=current_user.id,
        name=business_in.name,
        description=business_in.description,
        type=business_in.type,
    )
    db.add(business)
    await db.commit()
    return {"id": str(business.id), "name": business.name}


@router.get("/")
async def list_businesses(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List user's businesses."""
    result = await db.execute(
        select(Business).where(Business.user_id == current_user.id)
    )
    businesses = result.scalars().all()
    return [{"id": str(b.id), "name": b.name} for b in businesses]


@router.get("/{business_id}", response_model=BusinessResponse)
async def get_business(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Business).where(
            Business.id == business_id,
            Business.user_id == current_user.id,
        )
    )
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")
    return business


@router.put("/{business_id}", response_model=BusinessResponse)
async def update_business(
    business_id: UUID,
    business_in: BusinessUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Business).where(
            Business.id == business_id,
            Business.user_id == current_user.id,
        )
    )
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")

    update_data = business_in.model_dump(exclude_unset=True)
    if "config" in update_data and business.config:
        update_data["config"] = {**business.config, **update_data["config"]}

    for field, value in update_data.items():
        setattr(business, field, value)

    await db.commit()
    await db.refresh(business)
    return business


@router.delete("/{business_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_business(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Business).where(
            Business.id == business_id,
            Business.user_id == current_user.id,
        )
    )
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")

    business.is_active = False
    await db.commit()
    return None
