"""Base class for all specialized sales agents."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
from pydantic import BaseModel


class AgentType(str, Enum):
    """Agent specialization types."""
    DISCOVERY = "discovery"
    QUALIFICATION = "qualification"
    PROPOSAL = "proposal"
    OBJECTION_HANDLING = "objection_handling"
    NEGOTIATION = "negotiation"
    CLOSING = "closing"
    CS_RETENTION = "cs_retention"


class AgentContext(BaseModel):
    """Unified context passed between agents."""
    lead_id: str
    company: Optional[str] = None
    contact_name: Optional[str] = None
    decision_makers: List[str] = []
    intent_score: float = 0.0
    budget: Optional[str] = None
    timeline: Optional[str] = None
    source: Optional[str] = None
    current_stage: str = "lead_source"

    # Interaction history
    interaction_history: List[Dict[str, Any]] = []

    # Predictive signals
    close_probability: float = 0.0
    expected_deal_size: float = 0.0
    churn_risk: float = 0.0
    expansion_potential: float = 0.0

    # Competitive context
    main_competitor: Optional[str] = None
    differentiation_points: List[str] = []
    their_last_offer: Optional[str] = None

    # Agent metadata
    assigned_agent: Optional[str] = None
    agent_history: List[Dict[str, Any]] = []
    created_at: datetime = None
    updated_at: datetime = None

    class Config:
        json_schema_extra = {
            "example": {
                "lead_id": "lead_123",
                "company": "TechCorp Inc",
                "contact_name": "John Doe",
                "intent_score": 0.92,
                "budget": "$50k-$100k",
                "timeline": "Q4 2026",
                "current_stage": "discovery"
            }
        }


class AgentDecision(BaseModel):
    """Decision output from an agent."""
    next_agent: Optional[AgentType] = None
    action: str  # e.g., "send_email", "schedule_call", "escalate_to_human"
    confidence: float  # 0.0-1.0
    reasoning: str
    data: Dict[str, Any] = {}
    should_escalate: bool = False


class SalesAgent(ABC):
    """Base class for all specialized sales agents."""

    agent_type: AgentType
    name: str
    description: str

    def __init__(self):
        self.execution_count = 0
        self.success_count = 0
        self.avg_response_time = 0.0

    @abstractmethod
    async def evaluate(self, context: AgentContext) -> bool:
        """
        Determine if this agent should handle this lead.
        Returns True if agent is suitable for current context.
        """
        pass

    @abstractmethod
    async def execute(self, context: AgentContext) -> AgentDecision:
        """
        Execute agent logic and return decision + next action.
        """
        pass

    async def get_metrics(self) -> Dict[str, Any]:
        """Return agent performance metrics."""
        return {
            "name": self.name,
            "agent_type": self.agent_type.value,
            "description": self.description,
            "execution_count": self.execution_count,
            "success_count": self.success_count,
            "success_rate": self.success_rate,
            "avg_response_time_ms": self.avg_response_time,
        }

    def record_execution(self, success: bool, response_time_ms: float):
        """Record execution metrics."""
        self.execution_count += 1
        if success:
            self.success_count += 1

        # Update running average
        if self.avg_response_time == 0:
            self.avg_response_time = response_time_ms
        else:
            self.avg_response_time = (
                self.avg_response_time * 0.7 + response_time_ms * 0.3
            )

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.execution_count == 0:
            return 0.0
        return self.success_count / self.execution_count
