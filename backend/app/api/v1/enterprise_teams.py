from fastapi import APIRouter, Query, Body
from datetime import datetime
from app.domains.enterprise.team_management import (
    TeamManager,
    TeamMember,
    AgentType,
    TeamRole,
)

router = APIRouter(tags=["teams"])
team_manager = TeamManager()


@router.post("/teams/members/add")
async def add_team_member(
    user_id: str = Query(...),
    name: str = Query(...),
    email: str = Query(...),
    role: str = Query("agent", description="owner, manager, agent, viewer"),
    phone: str = Query(None),
):
    """Add team member."""
    try:
        role_enum = TeamRole(role)
        member = TeamMember(
            id=f"member_{datetime.now().timestamp()}",
            name=name,
            email=email,
            role=role_enum,
            status="active",
            joined_at=datetime.now(),
            phone=phone,
        )

        team_manager.add_team_member(user_id, member)

        return {
            "status": "added",
            "member_id": member.id,
            "name": name,
            "role": role,
        }
    except ValueError:
        return {"status": "error", "message": f"Invalid role: {role}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/teams/members/{user_id}")
async def list_team_members(user_id: str):
    """List all team members."""
    members = team_manager.get_team_members(user_id)

    return {
        "user_id": user_id,
        "total": len(members),
        "members": [
            {
                "id": m.id,
                "name": m.name,
                "email": m.email,
                "role": m.role.value,
                "status": m.status,
                "joined_at": m.joined_at.isoformat(),
            }
            for m in members
        ],
    }


@router.post("/teams/assign-agent")
async def assign_agent(
    user_id: str = Query(...),
    member_id: str = Query(...),
    agent_type: str = Query(..., description="lead_scout, closer_bot, coach_agent, analytics_engine"),
    workload_percentage: int = Query(100, ge=1, le=100),
):
    """Assign agent to team member."""
    try:
        agent_enum = AgentType(agent_type)
        success = team_manager.assign_agent(
            user_id,
            member_id,
            agent_enum,
            workload_percentage,
        )

        return {
            "status": "assigned" if success else "failed",
            "member_id": member_id,
            "agent": agent_type,
            "workload": workload_percentage,
        }
    except ValueError:
        return {"status": "error", "message": f"Invalid agent type: {agent_type}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.delete("/teams/unassign-agent")
async def unassign_agent(
    user_id: str = Query(...),
    assignment_id: str = Query(...),
):
    """Unassign agent from team member."""
    success = team_manager.unassign_agent(user_id, assignment_id)

    return {
        "status": "unassigned" if success else "not_found",
        "assignment_id": assignment_id,
    }


@router.get("/teams/assignments/{user_id}/{member_id}")
async def get_member_assignments(user_id: str, member_id: str):
    """Get agent assignments for team member."""
    assignments = team_manager.get_member_assignments(user_id, member_id)

    return {
        "member_id": member_id,
        "total_agents": len(assignments),
        "assignments": [
            {
                "id": a.id,
                "agent": a.agent_type.value,
                "workload": a.workload_percentage,
                "assigned_at": a.assigned_at.isoformat(),
                "is_primary": a.is_primary,
            }
            for a in assignments
        ],
    }


@router.get("/teams/performance/{user_id}/{member_id}")
async def get_member_performance(user_id: str, member_id: str):
    """Get performance metrics for team member."""
    perf = team_manager.get_member_performance(user_id, member_id)

    return {
        "member_id": perf.member_id,
        "member_name": perf.member_name,
        "assigned_agents": [a.value for a in perf.assigned_agents],
        "metrics": {
            "tasks_completed": perf.tasks_completed,
            "success_rate": f"{perf.success_rate}%",
            "avg_response_time": f"{perf.avg_response_time}s",
            "revenue_generated": f"${perf.revenue_generated:,.2f}",
            "lead_conversions": perf.lead_conversions,
            "customer_satisfaction": f"{perf.customer_satisfaction}/5.0",
        },
        "scores": {
            "workload": f"{perf.workload_score}/100",
            "efficiency": f"{perf.efficiency_score}/100",
        },
    }


@router.get("/teams/metrics/{user_id}")
async def get_team_metrics(user_id: str):
    """Get overall team metrics and health."""
    metrics = team_manager.get_team_metrics(user_id)

    return {
        "user_id": user_id,
        "team": {
            "total_members": metrics.total_members,
            "active_members": metrics.active_members,
            "total_agents_assigned": metrics.total_agents_assigned,
        },
        "performance": {
            "avg_efficiency": f"{metrics.avg_team_efficiency}/100",
            "total_revenue": f"${metrics.total_revenue_generated:,.2f}",
            "avg_response_time": f"{metrics.avg_response_time}s",
        },
        "top_performer": {
            "member_id": metrics.top_performer_id,
            "revenue": f"${metrics.top_performer_revenue:,.2f}" if metrics.top_performer_revenue else "$0.00",
        },
    }


@router.get("/teams/workload/{user_id}")
async def get_workload_distribution(user_id: str):
    """Get workload distribution across team."""
    distribution = team_manager.get_workload_distribution(user_id)

    return {
        "user_id": user_id,
        "distribution": distribution,
    }


@router.post("/teams/rebalance/{user_id}")
async def rebalance_workload(user_id: str):
    """Rebalance workload across team members."""
    result = team_manager.rebalance_workload(user_id)

    return {
        "user_id": user_id,
        **result,
    }


@router.post("/teams/delegate")
async def create_delegation(
    user_id: str = Query(...),
    from_member_id: str = Query(...),
    to_member_id: str = Query(...),
    agent_types: list[str] = Body(..., description="List of agent types"),
    reason: str = Query(...),
    duration_hours: int = Query(24),
):
    """Create delegation request."""
    try:
        agent_enums = [AgentType(a) for a in agent_types]
        delegation = team_manager.create_delegation(
            user_id,
            from_member_id,
            to_member_id,
            agent_enums,
            reason,
            duration_hours,
        )

        return {
            "status": "created",
            "delegation_id": delegation.id,
            "from": from_member_id,
            "to": to_member_id,
            "agents": agent_types,
            "expires_at": delegation.expires_at.isoformat() if delegation.expires_at else None,
        }
    except ValueError as e:
        return {"status": "error", "message": f"Invalid agent type: {str(e)}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/teams/delegation/{delegation_id}/approve")
async def approve_delegation(
    user_id: str = Query(...),
    delegation_id: str = Query(...),
):
    """Approve delegation request."""
    success = team_manager.approve_delegation(user_id, delegation_id)

    return {
        "status": "approved" if success else "not_found",
        "delegation_id": delegation_id,
    }


@router.post("/teams/delegation/{delegation_id}/reject")
async def reject_delegation(
    user_id: str = Query(...),
    delegation_id: str = Query(...),
):
    """Reject delegation request."""
    success = team_manager.reject_delegation(user_id, delegation_id)

    return {
        "status": "rejected" if success else "not_found",
        "delegation_id": delegation_id,
    }


@router.get("/teams/delegations/pending/{user_id}")
async def list_pending_delegations(user_id: str):
    """List pending delegation requests."""
    delegations = team_manager.get_pending_delegations(user_id)

    return {
        "user_id": user_id,
        "total_pending": len(delegations),
        "delegations": [
            {
                "id": d.id,
                "from": d.from_member_id,
                "to": d.to_member_id,
                "agents": [a.value for a in d.agent_types],
                "reason": d.reason,
                "created_at": d.created_at.isoformat(),
                "expires_at": d.expires_at.isoformat() if d.expires_at else None,
            }
            for d in delegations
        ],
    }
