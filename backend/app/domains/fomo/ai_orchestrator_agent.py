"""
Fase H: Multi-Agent Orchestrator

Coordinates the 7 previous FOMO agents (Fases A-G) without duplicating any
of their logic:
- AgentCatalog: static registry of what each agent does, for the dashboard
  and for anyone deciding what to call
- ContextRouter: given a business event, decides which agent(s) should
  activate and in what order — pure routing, doesn't invoke them itself
  (callers/routes own the actual HTTP/DB orchestration)
- ConflictResolver: when multiple agents want to message the SAME customer
  on the SAME day, picks one winner by priority (churn prevention outranks
  a general campaign — losing a customer matters more than one extra touch)
  and defers the rest with a reason and a suggested next send day
- UnifiedDashboard: aggregates already-computed decisions from any agent
  into one summary view, grouped by agent and by action taken
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional
from collections import defaultdict

from app.core.logger import get_logger

logger = get_logger(__name__)


class AgentCatalog:
    """Static registry of the 7 FOMO agents this orchestrator coordinates"""

    AGENTS = [
        {
            "id": "copywriter",
            "fase": "A",
            "name": "AI FOMO Copywriter Agent",
            "purpose": "Generates and ranks FOMO copy variants (subject/urgency/CTA/SMS)",
            "module": "ai_copywriter_agent",
        },
        {
            "id": "segmentation",
            "fase": "D",
            "name": "AI Customer Segmentation Agent",
            "purpose": "RFM-based segmentation + FOMO strategy per segment + fatigue exclusion",
            "module": "ai_segmentation_agent",
        },
        {
            "id": "timing",
            "fase": "B",
            "name": "AI Timing Optimizer Agent",
            "purpose": "Per-customer optimal send time + dynamic automation delays",
            "module": "ai_timing_optimizer_agent",
        },
        {
            "id": "scarcity",
            "fase": "C",
            "name": "AI Scarcity Calibration Agent",
            "purpose": "Truthful stock display, discount elasticity, urgency fatigue, A/B tests",
            "module": "ai_scarcity_calibration_agent",
        },
        {
            "id": "churn_prevention",
            "fase": "G",
            "name": "AI Predictive Churn-to-FOMO Agent",
            "purpose": "Churn risk scoring + win-back trigger + personalized offer sizing",
            "module": "ai_churn_prevention_agent",
        },
        {
            "id": "autonomous_campaign",
            "fase": "E",
            "name": "AI Autonomous Campaign Manager",
            "purpose": "Detects opportunities, builds campaigns, monitors ROI, pauses/scales",
            "module": "ai_autonomous_campaign_manager",
        },
        {
            "id": "competitor_monitor",
            "fase": "F",
            "name": "AI Competitor FOMO Monitor",
            "purpose": "Extracts competitor pricing signals, alerts on significant changes",
            "module": "ai_competitor_monitor_agent",
        },
    ]

    @staticmethod
    def list_agents() -> List[Dict[str, str]]:
        return AgentCatalog.AGENTS

    @staticmethod
    def get_agent(agent_id: str) -> Optional[Dict[str, str]]:
        return next((a for a in AgentCatalog.AGENTS if a["id"] == agent_id), None)


class ContextRouter:
    """Route a business event to the agent(s) that should handle it"""

    # event_type -> ordered list of (agent_id, reason)
    EVENT_AGENT_MAP: Dict[str, List[Dict[str, str]]] = {
        "new_visitor": [
            {"agent": "segmentation", "reason": "Classify the visitor into a segment for personalization"},
            {"agent": "copywriter", "reason": "Generate soft, non-pushy live-visitor widget copy"},
        ],
        "purchase_completed": [
            {"agent": "segmentation", "reason": "Update RFM standing with the new purchase"},
            {"agent": "timing", "reason": "Log the engagement point for future send-time prediction"},
        ],
        "cart_abandoned": [
            {"agent": "timing", "reason": "Predict this customer's best send time / adjust delays"},
            {"agent": "scarcity", "reason": "Calibrate truthful stock/discount messaging if applicable"},
            {"agent": "copywriter", "reason": "Generate the recovery sequence copy"},
        ],
        "stock_low": [
            {"agent": "scarcity", "reason": "Determine the truthful scarcity tier to display"},
            {"agent": "autonomous_campaign", "reason": "Decide whether to launch a scarcity campaign"},
        ],
        "seasonal_approaching": [
            {"agent": "autonomous_campaign", "reason": "Detects the seasonal opportunity and plans it"},
            {"agent": "copywriter", "reason": "Generate seasonal campaign copy"},
        ],
        "competitor_price_change": [
            {"agent": "competitor_monitor", "reason": "Confirm the change is significant and build the signal"},
            {"agent": "autonomous_campaign", "reason": "React to the competitor signal with a counter-campaign"},
            {"agent": "copywriter", "reason": "Generate the counter-offer messaging"},
        ],
        "customer_at_risk": [
            {"agent": "churn_prevention", "reason": "Already scored — this is the trigger for the win-back sequence"},
            {"agent": "timing", "reason": "Optimize the win-back send time for this specific customer"},
            {"agent": "copywriter", "reason": "Personalize the win-back offer copy"},
        ],
        "daily_tick": [
            {"agent": "autonomous_campaign", "reason": "Monitor running campaigns, pause/scale as needed"},
            {"agent": "churn_prevention", "reason": "Batch-scan customers for new churn risk"},
            {"agent": "scarcity", "reason": "Check urgency-intensity fatigue across active campaigns"},
        ],
    }

    @staticmethod
    def route_event(event_type: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Decide which agents should handle this event, in order"""
        plan = ContextRouter.EVENT_AGENT_MAP.get(event_type)

        if plan is None:
            return {
                "event_type": event_type,
                "known_event": False,
                "agents_to_invoke": [],
                "note": "Unrecognized event type — no routing rule configured",
            }

        return {
            "event_type": event_type,
            "known_event": True,
            "agents_to_invoke": [step["agent"] for step in plan],
            "execution_plan": plan,
            "context": context or {},
        }

    @staticmethod
    def list_known_events() -> List[str]:
        return list(ContextRouter.EVENT_AGENT_MAP.keys())


class ConflictResolver:
    """Resolve same-customer, same-day messaging conflicts between agents"""

    # Lower number = higher priority. Losing a customer (churn) outranks
    # reacting to a competitor or a general campaign touch.
    AGENT_PRIORITY = {
        "churn_prevention": 1,
        "autonomous_campaign": 2,
        "competitor_monitor": 2,
        "cart_abandonment": 3,
        "timing": 3,
        "segmentation": 4,
        "copywriter": 5,
    }

    DEFAULT_MAX_PER_DAY = 1

    @staticmethod
    def resolve(
        proposals: List[Dict[str, Any]],
        max_per_day: int = DEFAULT_MAX_PER_DAY,
    ) -> Dict[str, Any]:
        """proposals: [{"agent": str, "channel": str, "urgency": float (0-1, optional)}]
        all targeting the SAME customer on the SAME day."""
        if not proposals:
            return {"winners": [], "deferred": []}

        def sort_key(p: Dict[str, Any]) -> tuple:
            priority = ConflictResolver.AGENT_PRIORITY.get(p["agent"], 99)
            urgency = -(p.get("urgency") or 0.0)  # higher urgency sorts first
            return (priority, urgency)

        ranked = sorted(proposals, key=sort_key)

        winners = ranked[:max_per_day]
        deferred_raw = ranked[max_per_day:]

        deferred = [
            {
                **p,
                "reason": f"Daily message cap reached — {winners[0]['agent']} took priority today",
                "suggested_defer_to_days": 1,
            }
            for p in deferred_raw
        ]

        return {
            "winners": winners,
            "deferred": deferred,
            "total_proposals": len(proposals),
        }

    @staticmethod
    def resolve_batch(
        proposals_by_customer: Dict[str, List[Dict[str, Any]]],
        max_per_day: int = DEFAULT_MAX_PER_DAY,
    ) -> Dict[str, Any]:
        """Resolve conflicts across a batch of customers at once"""
        results = {}
        total_deferred = 0

        for customer_id, proposals in proposals_by_customer.items():
            result = ConflictResolver.resolve(proposals, max_per_day)
            results[customer_id] = result
            total_deferred += len(result["deferred"])

        return {
            "total_customers": len(proposals_by_customer),
            "total_deferred": total_deferred,
            "results": results,
        }


class UnifiedDashboard:
    """Aggregate already-computed agent decisions into one summary view"""

    @staticmethod
    def build_dashboard(
        agent_decisions: List[Dict[str, Any]],
        conflict_results: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """agent_decisions: [{"agent": str, "customer_id": Optional[str],
        "action": str, "timestamp": iso8601, "reason": Optional[str]}, ...]"""
        by_agent: Dict[str, int] = defaultdict(int)
        by_action: Dict[str, int] = defaultdict(int)

        for decision in agent_decisions:
            by_agent[decision["agent"]] += 1
            by_action[decision.get("action", "unknown")] += 1

        recent = sorted(
            agent_decisions,
            key=lambda d: d.get("timestamp", ""),
            reverse=True,
        )[:10]

        summary = {
            "total_decisions": len(agent_decisions),
            "decisions_by_agent": dict(by_agent),
            "decisions_by_action": dict(by_action),
            "most_recent": recent,
        }

        if conflict_results is not None:
            summary["conflicts"] = {
                "total_deferred": conflict_results.get("total_deferred", len(conflict_results.get("deferred", []))),
            }

        return summary


class AIOrchestratorAgent:
    """Fase H: Main agent — routes events, resolves conflicts, builds the
    unified dashboard. Does not re-implement any of the 7 agents' logic."""

    @staticmethod
    def get_agent_catalog() -> List[Dict[str, str]]:
        return AgentCatalog.list_agents()

    @staticmethod
    def route_event(event_type: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return ContextRouter.route_event(event_type, context)

    @staticmethod
    def list_known_events() -> List[str]:
        return ContextRouter.list_known_events()

    @staticmethod
    def resolve_conflicts(
        proposals: List[Dict[str, Any]],
        max_per_day: int = ConflictResolver.DEFAULT_MAX_PER_DAY,
    ) -> Dict[str, Any]:
        return ConflictResolver.resolve(proposals, max_per_day)

    @staticmethod
    def resolve_conflicts_batch(
        proposals_by_customer: Dict[str, List[Dict[str, Any]]],
        max_per_day: int = ConflictResolver.DEFAULT_MAX_PER_DAY,
    ) -> Dict[str, Any]:
        return ConflictResolver.resolve_batch(proposals_by_customer, max_per_day)

    @staticmethod
    def build_dashboard(
        agent_decisions: List[Dict[str, Any]],
        conflict_results: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return UnifiedDashboard.build_dashboard(agent_decisions, conflict_results)

    @staticmethod
    def handle_event_with_conflict_check(
        event_type: str,
        customer_id: str,
        context: Optional[Dict[str, Any]] = None,
        existing_proposals_today: Optional[List[Dict[str, Any]]] = None,
        max_per_day: int = ConflictResolver.DEFAULT_MAX_PER_DAY,
    ) -> Dict[str, Any]:
        """Route the event, then check whether the agents it would trigger
        conflict with anything already proposed for this customer today."""
        routing = ContextRouter.route_event(event_type, context)

        if not routing["known_event"]:
            return {**routing, "conflict_check": None}

        new_proposals = [
            {"agent": agent_id, "channel": "unspecified", "urgency": None}
            for agent_id in routing["agents_to_invoke"]
        ]
        all_proposals = (existing_proposals_today or []) + new_proposals

        conflict_check = ConflictResolver.resolve(all_proposals, max_per_day)

        return {**routing, "customer_id": customer_id, "conflict_check": conflict_check}
