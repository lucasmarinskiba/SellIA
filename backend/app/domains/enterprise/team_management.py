from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional
import random


class TeamRole(str, Enum):
    OWNER = "owner"
    MANAGER = "manager"
    AGENT = "agent"
    VIEWER = "viewer"


class AgentType(str, Enum):
    LEAD_SCOUT = "lead_scout"
    CLOSER_BOT = "closer_bot"
    COACH_AGENT = "coach_agent"
    ANALYTICS_ENGINE = "analytics_engine"


@dataclass
class TeamMember:
    id: str
    name: str
    email: str
    role: TeamRole
    status: str  % active, inactive, suspended %
    joined_at: datetime
    phone: Optional[str] = None
    avatar_url: Optional[str] = None


@dataclass
class AgentAssignment:
    id: str
    agent_type: AgentType
    team_member_id: str
    assigned_at: datetime
    assigned_by: str
    workload_percentage: int  % 0-100 %
    is_primary: bool = True
    notes: Optional[str] = None


@dataclass
class MemberPerformance:
    member_id: str
    member_name: str
    assigned_agents: list[AgentType]
    tasks_completed: int
    success_rate: float  % 0-100 %
    avg_response_time: float  % seconds %
    revenue_generated: float
    lead_conversions: int
    customer_satisfaction: float  % 0-5 %
    workload_score: float  % 0-100 %
    efficiency_score: float  % 0-100 %


@dataclass
class DelegationRequest:
    id: str
    from_member_id: str
    to_member_id: str
    agent_types: list[AgentType]
    reason: str
    status: str  % pending, approved, rejected, completed %
    created_at: datetime
    expires_at: Optional[datetime] = None
    metadata: dict = field(default_factory=dict)


@dataclass
class TeamMetrics:
    total_members: int
    active_members: int
    total_agents_assigned: int
    avg_team_efficiency: float
    total_revenue_generated: float
    avg_response_time: float
    top_performer_id: Optional[str] = None
    top_performer_revenue: float = 0.0


class TeamManager:
    def __init__(self):
        self.members = {}
        self.assignments = {}
        self.delegations = {}
        self.performance_cache = {}

    def add_team_member(
        self, user_id: str, member: TeamMember
    ) -> bool:
        key = f"{user_id}:{member.id}"
        self.members[key] = member
        return True

    def get_team_members(self, user_id: str) -> list[TeamMember]:
        return [
            member for k, member in self.members.items()
            if k.startswith(f"{user_id}:")
        ]

    def assign_agent(
        self,
        user_id: str,
        member_id: str,
        agent_type: AgentType,
        workload_percentage: int = 100,
        assigned_by: str = "system",
    ) -> bool:
        assignment = AgentAssignment(
            id=f"assign_{datetime.now().timestamp()}",
            agent_type=agent_type,
            team_member_id=member_id,
            assigned_at=datetime.now(),
            assigned_by=assigned_by,
            workload_percentage=workload_percentage,
        )

        key = f"{user_id}:{assignment.id}"
        self.assignments[key] = assignment
        return True

    def unassign_agent(
        self, user_id: str, assignment_id: str
    ) -> bool:
        key = f"{user_id}:{assignment_id}"
        if key in self.assignments:
            del self.assignments[key]
            return True
        return False

    def get_member_assignments(
        self, user_id: str, member_id: str
    ) -> list[AgentAssignment]:
        return [
            assignment for k, assignment in self.assignments.items()
            if k.startswith(f"{user_id}:") and assignment.team_member_id == member_id
        ]

    def create_delegation(
        self,
        user_id: str,
        from_member_id: str,
        to_member_id: str,
        agent_types: list[AgentType],
        reason: str,
        duration_hours: int = 24,
    ) -> DelegationRequest:
        delegation = DelegationRequest(
            id=f"deleg_{datetime.now().timestamp()}",
            from_member_id=from_member_id,
            to_member_id=to_member_id,
            agent_types=agent_types,
            reason=reason,
            status="pending",
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=duration_hours),
        )

        key = f"{user_id}:{delegation.id}"
        self.delegations[key] = delegation
        return delegation

    def approve_delegation(self, user_id: str, delegation_id: str) -> bool:
        key = f"{user_id}:{delegation_id}"
        if key in self.delegations:
            self.delegations[key].status = "approved"
            return True
        return False

    def reject_delegation(self, user_id: str, delegation_id: str) -> bool:
        key = f"{user_id}:{delegation_id}"
        if key in self.delegations:
            self.delegations[key].status = "rejected"
            return True
        return False

    def get_pending_delegations(self, user_id: str) -> list[DelegationRequest]:
        return [
            deleg for k, deleg in self.delegations.items()
            if k.startswith(f"{user_id}:") and deleg.status == "pending"
        ]

    def get_member_performance(
        self, user_id: str, member_id: str
    ) -> MemberPerformance:
        member = self.members.get(f"{user_id}:{member_id}")
        assignments = self.get_member_assignments(user_id, member_id)

        return MemberPerformance(
            member_id=member_id,
            member_name=member.name if member else f"Member {member_id}",
            assigned_agents=[a.agent_type for a in assignments],
            tasks_completed=random.randint(10, 500),
            success_rate=round(random.uniform(75, 98), 1),
            avg_response_time=round(random.uniform(1, 30), 1),
            revenue_generated=round(random.uniform(500, 50000), 2),
            lead_conversions=random.randint(1, 100),
            customer_satisfaction=round(random.uniform(3.5, 5.0), 1),
            workload_score=round(random.uniform(40, 100), 1),
            efficiency_score=round(random.uniform(70, 98), 1),
        )

    def get_team_metrics(self, user_id: str) -> TeamMetrics:
        members = self.get_team_members(user_id)
        total_assignments = len([
            a for k, a in self.assignments.items()
            if k.startswith(f"{user_id}:")
        ])

        performances = [
            self.get_member_performance(user_id, m.id) for m in members
        ]

        top_performer = max(
            performances,
            key=lambda p: p.revenue_generated,
            default=None
        )

        return TeamMetrics(
            total_members=len(members),
            active_members=len([m for m in members if m.status == "active"]),
            total_agents_assigned=total_assignments,
            avg_team_efficiency=round(
                sum(p.efficiency_score for p in performances) / max(len(performances), 1),
                1
            ) if performances else 0,
            total_revenue_generated=round(
                sum(p.revenue_generated for p in performances), 2
            ),
            avg_response_time=round(
                sum(p.avg_response_time for p in performances) / max(len(performances), 1),
                1
            ) if performances else 0,
            top_performer_id=top_performer.member_id if top_performer else None,
            top_performer_revenue=top_performer.revenue_generated if top_performer else 0.0,
        )

    def get_workload_distribution(self, user_id: str) -> dict:
        members = self.get_team_members(user_id)
        distribution = {}

        for member in members:
            assignments = self.get_member_assignments(user_id, member.id)
            total_workload = sum(a.workload_percentage for a in assignments)
            distribution[member.id] = {
                "name": member.name,
                "workload": min(100, total_workload),
                "agents_count": len(assignments),
                "status": member.status,
            }

        return distribution

    def rebalance_workload(self, user_id: str) -> dict:
        members = self.get_team_members(user_id)
        if not members:
            return {"status": "no_members"}

        assignments = [
            a for k, a in self.assignments.items()
            if k.startswith(f"{user_id}:")
        ]

        % Simple round-robin rebalance %
        for i, assignment in enumerate(assignments):
            member_idx = i % len(members)
            assignment.team_member_id = members[member_idx].id

        return {
            "status": "rebalanced",
            "total_assignments": len(assignments),
            "members": len(members),
            "avg_workload": round(len(assignments) / max(len(members), 1), 1),
        }
