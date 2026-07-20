"""Swarm API Router — Multi-Agent Collaboration Endpoints."""

from uuid import UUID
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.domains.users.models import User
from app.domains.businesses.models import Business
from app.domains.agents.swarm import AgentSwarm, SwarmCoordinator
from app.domains.agents.swarm_memory import SwarmSession, SwarmMessage
from app.domains.agents.schemas import (
    SwarmExecuteRequest,
    SwarmExecuteResponse,
    SwarmSessionResponse,
    SwarmMessageResponse,
    SwarmSuggestRequest,
    SwarmSuggestResponse,
    SwarmSuggestedAgent,
    SwarmAgentContribution,
)

router = APIRouter()


@router.post("/execute", response_model=SwarmExecuteResponse)
async def execute_swarm(
    data: SwarmExecuteRequest,
    business_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Execute a multi-agent swarm task."""
    if business_id:
        result = await db.execute(
            select(Business).where(Business.id == business_id).where(Business.user_id == current_user.id)
        )
        business = result.scalar_one_or_none()
        if not business:
            raise HTTPException(status_code=404, detail="Negocio no encontrado")

    swarm = AgentSwarm(db=db, business_id=business_id)
    result = await swarm.execute_swarm(
        task=data.task,
        agents=data.agents,
        context=data.context,
        consensus_required=data.consensus_required,
        max_rounds=data.max_rounds,
    )

    return SwarmExecuteResponse(
        session_id=result["session_id"],
        final_response=result["final_response"],
        agent_contributions=[SwarmAgentContribution.model_validate(m) for m in result["agent_contributions"]],
        reasoning=result["reasoning"],
        consensus_reached=result["consensus_reached"],
        rounds=result["rounds"],
    )


@router.get("/sessions", response_model=List[SwarmSessionResponse])
async def list_swarm_sessions(
    business_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List swarm sessions for the current user."""
    query = select(SwarmSession)

    if business_id:
        result = await db.execute(
            select(Business).where(Business.id == business_id).where(Business.user_id == current_user.id)
        )
        business = result.scalar_one_or_none()
        if not business:
            raise HTTPException(status_code=404, detail="Negocio no encontrado")
        query = query.where(SwarmSession.business_id == business_id)
    else:
        # Filter by user's businesses
        result = await db.execute(
            select(Business.id).where(Business.user_id == current_user.id)
        )
        business_ids = [r[0] for r in result.all()]
        query = query.where(SwarmSession.business_id.in_(business_ids))

    query = query.order_by(desc(SwarmSession.created_at))
    result = await db.execute(query)
    sessions = result.scalars().all()

    response = []
    for session in sessions:
        msg_result = await db.execute(
            select(SwarmMessage).where(SwarmMessage.session_id == session.id).order_by(SwarmMessage.created_at)
        )
        messages = msg_result.scalars().all()
        session_data = SwarmSessionResponse.model_validate(session)
        session_data.messages = [SwarmMessageResponse.model_validate(m) for m in messages]
        response.append(session_data)

    return response


@router.get("/sessions/{session_id}", response_model=SwarmSessionResponse)
async def get_swarm_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get a single swarm session with all messages."""
    result = await db.execute(
        select(SwarmSession).where(SwarmSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")

    # Verify ownership via business
    result = await db.execute(
        select(Business).where(Business.id == session.business_id).where(Business.user_id == current_user.id)
    )
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=403, detail="No tenés acceso a esta sesión")

    msg_result = await db.execute(
        select(SwarmMessage).where(SwarmMessage.session_id == session.id).order_by(SwarmMessage.created_at)
    )
    messages = msg_result.scalars().all()

    session_data = SwarmSessionResponse.model_validate(session)
    session_data.messages = [SwarmMessageResponse.model_validate(m) for m in messages]
    return session_data


@router.post("/suggest-agents", response_model=SwarmSuggestResponse)
async def suggest_agents(
    data: SwarmSuggestRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Suggest agents and roles for a given task."""
    coordinator = SwarmCoordinator()
    suggestions = coordinator.assign_roles(data.task)
    return SwarmSuggestResponse(
        suggested_agents=[SwarmSuggestedAgent.model_validate(s) for s in suggestions]
    )
