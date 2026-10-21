"""Fase H: Multi-Agent Orchestrator — API routes"""

from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, Query

from app.core.deps import get_current_user
from app.domains.fomo.ai_orchestrator_agent import (
    AIOrchestratorAgent,
    ConflictResolver,
)
from app.domains.users.models import User

router = APIRouter(prefix="/fomo/ai/orchestrator", tags=["fomo-ai-orchestrator"])


@router.get("/agents")
async def get_agent_catalog(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """List all 7 FOMO agents this orchestrator coordinates"""
    return {"agents": AIOrchestratorAgent.get_agent_catalog()}


@router.get("/events")
async def list_known_events(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """List all business event types with a configured routing rule"""
    return {"events": AIOrchestratorAgent.list_known_events()}


@router.get("/route-event")
async def route_event(
    event_type: Annotated[str, Query()],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Decide which agent(s) should handle a given business event, in order"""
    return AIOrchestratorAgent.route_event(event_type)


@router.post("/resolve-conflicts")
async def resolve_conflicts(
    proposals: Annotated[list[dict[str, Any]], Body(description='[{"agent": str, "channel": str, "urgency": float}] for ONE customer, ONE day')],
    current_user: Annotated[User, Depends(get_current_user)],
    max_per_day: Annotated[int, Query(ge=1)] = ConflictResolver.DEFAULT_MAX_PER_DAY,
):
    """Resolve same-customer same-day messaging conflicts between agents"""
    return AIOrchestratorAgent.resolve_conflicts(proposals, max_per_day)


@router.post("/resolve-conflicts-batch")
async def resolve_conflicts_batch(
    proposals_by_customer: Annotated[dict[str, list[dict[str, Any]]], Body()],
    current_user: Annotated[User, Depends(get_current_user)],
    max_per_day: Annotated[int, Query(ge=1)] = ConflictResolver.DEFAULT_MAX_PER_DAY,
):
    """Resolve conflicts across a batch of customers at once"""
    return AIOrchestratorAgent.resolve_conflicts_batch(proposals_by_customer, max_per_day)


@router.post("/dashboard")
async def build_dashboard(
    agent_decisions: Annotated[list[dict[str, Any]], Body()],
    current_user: Annotated[User, Depends(get_current_user)],
    conflict_results: Annotated[dict[str, Any] | None, Body()] = None,
):
    """Build a unified summary dashboard from already-computed agent decisions"""
    return AIOrchestratorAgent.build_dashboard(agent_decisions, conflict_results)


@router.post("/handle-event")
async def handle_event_with_conflict_check(
    event_type: Annotated[str, Query()],
    customer_id: Annotated[str, Query()],
    current_user: Annotated[User, Depends(get_current_user)],
    existing_proposals_today: Annotated[list[dict[str, Any]] | None, Body()] = None,
    max_per_day: Annotated[int, Query(ge=1)] = ConflictResolver.DEFAULT_MAX_PER_DAY,
):
    """Route an event for one customer and check it against today's existing proposals"""
    return AIOrchestratorAgent.handle_event_with_conflict_check(
        event_type, customer_id, existing_proposals_today=existing_proposals_today, max_per_day=max_per_day
    )
