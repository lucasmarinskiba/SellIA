"""Human escalation queue system for leads requiring human intervention."""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class EscalationReason(str, Enum):
    """Reasons for escalation to human rep."""
    LOW_INTENT = "low_intent"  # Intent <0.3
    COMPLEX_OBJECTION = "complex_objection"  # Multiple unresolved objections
    BUDGET_NEGOTIATION = "budget_negotiation"  # Needs discount authority override
    LEGAL_REVIEW = "legal_review"  # Contract needs legal review
    VIP_ACCOUNT = "vip_account"  # Executive or high-value deal
    AGENT_ERROR = "agent_error"  # Agent execution failure
    MANUAL_REQUEST = "manual_request"  # Customer requested human
    STALLED_DEAL = "stalled_deal"  # No engagement for 7+ days


class EscalationPriority(str, Enum):
    """Queue priority levels."""
    CRITICAL = "critical"  # VIP, legal required, escalated multiple times
    HIGH = "high"  # High deal size, complex objections
    MEDIUM = "medium"  # Standard escalations
    LOW = "low"  # Low intent, can wait


@dataclass
class EscalationTicket:
    """Escalation ticket in queue."""
    ticket_id: str
    lead_id: str
    lead_name: str
    company: str
    reason: EscalationReason
    priority: EscalationPriority
    deal_size: float
    agent_notes: str
    created_at: datetime
    assigned_to: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    status: str = "pending"  # pending, in_progress, resolved


class EscalationQueue:
    """Queue for managing human escalations."""

    def __init__(self):
        self.tickets: Dict[str, EscalationTicket] = {}
        self.reps: Dict[str, Dict[str, Any]] = {
            "rep_001": {"name": "Alice Johnson", "queue": [], "capacity": 10, "current_load": 0},
            "rep_002": {"name": "Bob Smith", "queue": [], "capacity": 10, "current_load": 0},
            "rep_003": {"name": "Carol White", "queue": [], "capacity": 8, "current_load": 0},
        }

    async def create_ticket(
        self,
        lead_id: str,
        lead_name: str,
        company: str,
        reason: EscalationReason,
        deal_size: float,
        agent_notes: str,
    ) -> EscalationTicket:
        """Create escalation ticket."""
        # Determine priority
        if reason in [EscalationReason.VIP_ACCOUNT, EscalationReason.LEGAL_REVIEW]:
            priority = EscalationPriority.CRITICAL
        elif deal_size > 100000:
            priority = EscalationPriority.HIGH
        elif deal_size > 50000:
            priority = EscalationPriority.MEDIUM
        else:
            priority = EscalationPriority.LOW

        ticket_id = f"esc_{datetime.now().timestamp()}"
        ticket = EscalationTicket(
            ticket_id=ticket_id,
            lead_id=lead_id,
            lead_name=lead_name,
            company=company,
            reason=reason,
            priority=priority,
            deal_size=deal_size,
            agent_notes=agent_notes,
            created_at=datetime.utcnow(),
        )

        self.tickets[ticket_id] = ticket

        # Auto-assign to least loaded rep
        assigned_rep = self._find_best_rep(priority)
        if assigned_rep:
            ticket.assigned_to = assigned_rep
            self.reps[assigned_rep]["queue"].append(ticket_id)
            self.reps[assigned_rep]["current_load"] += 1

        logger.info(f"Escalation created: {ticket_id} for {lead_name} (priority={priority.value})")
        return ticket

    def _find_best_rep(self, priority: EscalationPriority) -> Optional[str]:
        """Find best sales rep based on priority and capacity."""
        # Get available reps
        available = [
            (rep_id, data)
            for rep_id, data in self.reps.items()
            if data["current_load"] < data["capacity"]
        ]

        if not available:
            logger.warning(f"No capacity for escalation (priority={priority.value})")
            return None

        # Sort by load (ascending)
        available.sort(key=lambda x: x[1]["current_load"])
        return available[0][0]

    async def get_queue(self, rep_id: Optional[str] = None) -> List[EscalationTicket]:
        """Get escalation queue."""
        if rep_id:
            ticket_ids = self.reps[rep_id]["queue"]
            return [self.tickets[tid] for tid in ticket_ids if self.tickets[tid].status != "resolved"]

        # Return all pending tickets sorted by priority
        pending = [t for t in self.tickets.values() if t.status != "resolved"]
        priority_order = {
            EscalationPriority.CRITICAL: 0,
            EscalationPriority.HIGH: 1,
            EscalationPriority.MEDIUM: 2,
            EscalationPriority.LOW: 3,
        }
        pending.sort(key=lambda t: (priority_order[t.priority], t.created_at))
        return pending

    async def resolve_ticket(
        self,
        ticket_id: str,
        resolution_notes: str,
        outcome: str = "closed_won",  # closed_won, closed_lost, handoff_to_agent
    ) -> bool:
        """Resolve an escalation ticket."""
        if ticket_id not in self.tickets:
            return False

        ticket = self.tickets[ticket_id]
        ticket.status = "resolved"
        ticket.resolved_at = datetime.utcnow()
        ticket.resolution_notes = resolution_notes

        # Update rep load
        if ticket.assigned_to:
            self.reps[ticket.assigned_to]["current_load"] -= 1
            self.reps[ticket.assigned_to]["queue"].remove(ticket_id)

        logger.info(f"Ticket {ticket_id} resolved: {outcome}")
        return True

    async def sla_check(self) -> Dict[str, Any]:
        """Check SLA compliance (response time, resolution time)."""
        sla_targets = {
            EscalationPriority.CRITICAL: 1,  # 1 hour
            EscalationPriority.HIGH: 4,  # 4 hours
            EscalationPriority.MEDIUM: 24,  # 24 hours
            EscalationPriority.LOW: 72,  # 72 hours
        }

        breaches = []
        for ticket in self.tickets.values():
            if ticket.status == "resolved":
                continue

            age_hours = (datetime.utcnow() - ticket.created_at).total_seconds() / 3600
            sla_hours = sla_targets[ticket.priority]

            if age_hours > sla_hours:
                breaches.append(
                    {
                        "ticket_id": ticket.ticket_id,
                        "lead": ticket.lead_name,
                        "priority": ticket.priority.value,
                        "age_hours": round(age_hours, 1),
                        "sla_hours": sla_hours,
                        "overdue_hours": round(age_hours - sla_hours, 1),
                    }
                )

        return {
            "total_tickets": len(self.tickets),
            "pending": sum(1 for t in self.tickets.values() if t.status != "resolved"),
            "sla_breaches": len(breaches),
            "breached_tickets": breaches,
        }


# Global queue instance
escalation_queue = EscalationQueue()
