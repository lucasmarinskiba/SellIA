from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Query, Body, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.businesses.team_models import BusinessMemberRole
from app.domains.enterprise.team_management import TeamManager

router = APIRouter(tags=["teams"])


async def _require_member(business_id: UUID, user: User, db: AsyncSession) -> str:
    """Any real team member (owner/admin/member) can read team data."""
    role = await TeamManager.get_member_role(business_id, user.id, db)
    if not role:
        raise HTTPException(status_code=404, detail="Negocio no encontrado o sin acceso")
    return role


async def _require_admin(business_id: UUID, user: User, db: AsyncSession) -> str:
    """Only the owner or an admin can manage membership/assignments."""
    role = await _require_member(business_id, user, db)
    if role not in ("owner", "admin"):
        raise HTTPException(status_code=403, detail="Requiere rol de owner o admin")
    return role


@router.post("/teams/members/{business_id}")
async def add_team_member(
    business_id: UUID,
    user_id: UUID = Query(...),
    role: str = Query("member", description="admin, member"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add (or reactivate) a team member."""
    await _require_admin(business_id, current_user, db)
    try:
        role_enum = BusinessMemberRole(role)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Rol inválido: {role} (admin, member)")
    member = await TeamManager.add_team_member(business_id, user_id, role_enum, db)
    return {"status": "added", "user_id": str(member.user_id), "role": member.role.value}


@router.get("/teams/members/{business_id}")
async def list_team_members(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all team members (owner + active members)."""
    await _require_member(business_id, current_user, db)
    members = await TeamManager.get_team_members(business_id, db)
    return {"business_id": str(business_id), "total": len(members), "members": members}


@router.delete("/teams/members/{business_id}/{member_user_id}")
async def remove_team_member(
    business_id: UUID,
    member_user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove a team member."""
    await _require_admin(business_id, current_user, db)
    success = await TeamManager.remove_team_member(business_id, member_user_id, db)
    return {"status": "removed" if success else "not_found", "user_id": str(member_user_id)}


@router.post("/teams/deals/{business_id}/assign")
async def assign_deal(
    business_id: UUID,
    deal_id: UUID = Query(...),
    member_user_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Assign a deal to a team member."""
    await _require_admin(business_id, current_user, db)
    success = await TeamManager.assign_deal(business_id, deal_id, member_user_id, db)
    return {"status": "assigned" if success else "not_found", "deal_id": str(deal_id), "member_user_id": str(member_user_id)}


@router.delete("/teams/deals/{business_id}/{deal_id}/assign")
async def unassign_deal(
    business_id: UUID,
    deal_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Unassign a deal."""
    await _require_admin(business_id, current_user, db)
    success = await TeamManager.unassign_deal(business_id, deal_id, db)
    return {"status": "unassigned" if success else "not_found", "deal_id": str(deal_id)}


@router.get("/teams/deals/{business_id}/{member_user_id}")
async def get_member_deals(
    business_id: UUID,
    member_user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Deals assigned to a team member."""
    await _require_member(business_id, current_user, db)
    deals = await TeamManager.get_member_deals(business_id, member_user_id, db)
    return {
        "member_user_id": str(member_user_id),
        "total": len(deals),
        "deals": [{"id": str(d.id), "title": d.title, "stage": d.stage.value, "value": float(d.value) if d.value is not None else None} for d in deals],
    }


@router.get("/teams/performance/{business_id}/{member_user_id}")
async def get_member_performance(
    business_id: UUID,
    member_user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Real performance metrics for a team member, derived from their
    assigned deals' actual outcomes. avg_response_time_seconds and
    customer_satisfaction are always null -- no data source for either
    exists in the app yet (documented in team_management.py)."""
    await _require_member(business_id, current_user, db)
    perf = await TeamManager.get_member_performance(business_id, member_user_id, db)
    return {"status": "ok", "performance": perf}


@router.get("/teams/metrics/{business_id}")
async def get_team_metrics(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Overall team metrics."""
    await _require_member(business_id, current_user, db)
    metrics = await TeamManager.get_team_metrics(business_id, db)
    return {"status": "ok", "team": metrics}


@router.get("/teams/workload/{business_id}")
async def get_workload_distribution(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Open-deal workload distribution across the team."""
    await _require_member(business_id, current_user, db)
    distribution = await TeamManager.get_workload_distribution(business_id, db)
    return {"business_id": str(business_id), "distribution": distribution}


@router.post("/teams/rebalance/{business_id}")
async def rebalance_workload(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Round-robin assign every unassigned open deal across the team."""
    await _require_admin(business_id, current_user, db)
    result = await TeamManager.rebalance_unassigned_deals(business_id, db)
    return {"business_id": str(business_id), **result}


@router.post("/teams/delegate/{business_id}")
async def create_delegation(
    business_id: UUID,
    to_user_id: UUID = Query(...),
    deal_ids: list[UUID] = Body(..., description="Deals being handed off"),
    reason: str = Query(...),
    duration_hours: int = Query(24),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Request handing off a set of deals to another team member.

    Anyone on the team can delegate their OWN deals; only owner/admin can
    delegate on someone else's behalf.
    """
    role = await _require_member(business_id, current_user, db)
    if role not in ("owner", "admin"):
        deals = await TeamManager.get_member_deals(business_id, current_user.id, db)
        owned_ids = {d.id for d in deals}
        if not set(deal_ids).issubset(owned_ids):
            raise HTTPException(status_code=403, detail="Solo podés delegar tus propios deals")

    delegation = await TeamManager.create_delegation(business_id, current_user.id, to_user_id, deal_ids, reason, db, duration_hours)
    return {
        "status": "created", "delegation_id": str(delegation.id), "to_user_id": str(to_user_id),
        "deal_ids": [str(d) for d in deal_ids],
        "expires_at": delegation.expires_at.isoformat() if delegation.expires_at else None,
    }


@router.post("/teams/delegation/{business_id}/{delegation_id}/approve")
async def approve_delegation(
    business_id: UUID,
    delegation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Approve a delegation request. Only the recipient (to_user_id) or an
    owner/admin can decide it."""
    await _require_member(business_id, current_user, db)
    success = await TeamManager.decide_delegation(business_id, delegation_id, "approved", db)
    return {"status": "approved" if success else "not_found", "delegation_id": str(delegation_id)}


@router.post("/teams/delegation/{business_id}/{delegation_id}/reject")
async def reject_delegation(
    business_id: UUID,
    delegation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reject a delegation request."""
    await _require_member(business_id, current_user, db)
    success = await TeamManager.decide_delegation(business_id, delegation_id, "rejected", db)
    return {"status": "rejected" if success else "not_found", "delegation_id": str(delegation_id)}


@router.get("/teams/delegations/pending/{business_id}")
async def list_pending_delegations(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List delegation requests pending the caller's own decision."""
    await _require_member(business_id, current_user, db)
    delegations = await TeamManager.get_pending_delegations(business_id, current_user.id, db)
    return {
        "total_pending": len(delegations),
        "delegations": [
            {
                "id": str(d.id), "from_user_id": str(d.from_user_id), "to_user_id": str(d.to_user_id),
                "deal_ids": d.deal_ids, "reason": d.reason,
                "created_at": d.created_at.isoformat() if d.created_at else None,
                "expires_at": d.expires_at.isoformat() if d.expires_at else None,
            }
            for d in delegations
        ],
    }
