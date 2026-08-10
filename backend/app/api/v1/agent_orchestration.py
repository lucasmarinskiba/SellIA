"""
Agent Orchestration API - Multi-agent routing and orchestration endpoints.
Phase 7: Multi-Agent Orchestration
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

from app.domains.agents.agent_router import AgentRouter
from app.domains.agents.base_agent import AgentContext, AgentType
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["agent-orchestration"])
agent_router = AgentRouter()

logger = logging.getLogger(__name__)


class RouteLeadRequest:
    """Request to route a lead through the agent pipeline."""

    def __init__(
        self,
        lead_id: str,
        company: Optional[str] = None,
        contact_name: Optional[str] = None,
        intent_score: float = 0.5,
        budget: Optional[str] = None,
        timeline: Optional[str] = None,
        source: Optional[str] = None,
    ):
        self.lead_id = lead_id
        self.company = company
        self.contact_name = contact_name
        self.intent_score = intent_score
        self.budget = budget
        self.timeline = timeline
        self.source = source


@router.post("/orchestrate/route-lead")
async def route_lead(
    lead_id: str = Query(..., description="Unique lead identifier"),
    company: Optional[str] = Query(None, description="Company name"),
    contact_name: Optional[str] = Query(None, description="Contact person name"),
    intent_score: float = Query(0.5, ge=0.0, le=1.0, description="Intent score 0-1"),
    budget: Optional[str] = Query(None, description="Budget range"),
    timeline: Optional[str] = Query(None, description="Purchasing timeline"),
    source: Optional[str] = Query(None, description="Lead source"),
) -> Dict[str, Any]:
    """
    Route a lead through the agent pipeline.

    The router will:
    1. Evaluate the lead context
    2. Select the best agent for current stage
    3. Execute agent logic
    4. Advance to next agent or escalate
    5. Return final decision or escalation status

    **Possible outcomes:**
    - `completed`: Lead advanced through full pipeline
    - `escalated`: Handed off to human sales representative
    - `error`: Pipeline error requiring intervention
    """
    try:
        # Create context
        context = AgentContext(
            lead_id=lead_id,
            company=company,
            contact_name=contact_name,
            intent_score=intent_score,
            budget=budget,
            timeline=timeline,
            source=source,
            current_stage="lead_source",
            created_at=datetime.utcnow(),
        )

        logger.info(f"Starting lead routing for {lead_id}: {company}")

        # Route through agent pipeline
        result = await agent_router.route_lead(context)

        return {
            "status": "success",
            "routing_result": result,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.exception(f"Lead routing failed: {lead_id}")
        raise HTTPException(status_code=500, detail=f"Routing failed: {str(e)}")


@router.post("/orchestrate/batch-route")
async def batch_route_leads(
    leads: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Route multiple leads in parallel for high-throughput processing.

    Request body example:
    ```json
    {
      "leads": [
        {
          "lead_id": "lead_1",
          "company": "TechCorp",
          "intent_score": 0.85
        },
        {
          "lead_id": "lead_2",
          "company": "CloudInc",
          "intent_score": 0.70
        }
      ]
    }
    ```
    """
    if not leads:
        raise HTTPException(status_code=400, detail="No leads provided")

    try:
        contexts = [
            AgentContext(
                lead_id=lead.get("lead_id", f"lead_{i}"),
                company=lead.get("company"),
                contact_name=lead.get("contact_name"),
                intent_score=lead.get("intent_score", 0.5),
                budget=lead.get("budget"),
                timeline=lead.get("timeline"),
                source=lead.get("source", "batch_import"),
                current_stage="lead_source",
                created_at=datetime.utcnow(),
            )
            for i, lead in enumerate(leads)
        ]

        logger.info(f"Batch routing {len(leads)} leads")
        results = await agent_router.batch_route_leads(contexts)

        return {
            "status": "success",
            "leads_processed": len(results),
            "results": results,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.exception("Batch routing failed")
        raise HTTPException(status_code=500, detail=f"Batch routing failed: {str(e)}")


@router.get("/orchestrate/agent-performance")
async def get_agent_performance() -> Dict[str, Any]:
    """
    Get real-time performance metrics for all agents.

    Returns:
    - Execution count
    - Success rate
    - Average response time
    - Current workload
    """
    try:
        performance = await agent_router.get_agent_performance()

        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "agents": performance,
            "summary": {
                "total_agents": len(performance),
                "avg_success_rate": sum(
                    a.get("success_rate", 0) for a in performance.values()
                )
                / len(performance),
                "total_executions": sum(
                    a.get("execution_count", 0) for a in performance.values()
                ),
            },
        }

    except Exception as e:
        logger.exception("Performance retrieval failed")
        raise HTTPException(
            status_code=500, detail=f"Performance retrieval failed: {str(e)}"
        )


@router.get("/orchestrate/agents")
async def list_agents() -> Dict[str, Any]:
    """List all available agents with their specializations."""
    agents_info = []

    for agent_type, agent in {
        AgentType.DISCOVERY: "Handles cold lead research and initial outreach",
        AgentType.QUALIFICATION: "BANT scoring and fit validation",
        AgentType.PROPOSAL: "Custom deck generation and pricing",
        AgentType.OBJECTION_HANDLING: "Objection rebuttal and social proof",
        AgentType.NEGOTIATION: "Terms negotiation and discount authority",
        AgentType.CLOSING: "Signature automation and handoff",
        AgentType.CS_RETENTION: "Onboarding, upsell, and retention",
    }.items():
        agents_info.append(
            {
                "type": agent_type.value,
                "name": f"{agent_type.value.replace('_', ' ').title()} Agent",
                "description": agent,
                "pipeline_stage": agent_type.value,
            }
        )

    return {
        "status": "success",
        "agents": agents_info,
        "total": len(agents_info),
        "@context": "https://schema.org",
        "@type": "Dataset",
        "name": "SellIA Agent Registry",
    }


@router.get("/orchestrate/workflow-example")
async def get_workflow_example() -> Dict[str, Any]:
    """Get example lead flow through all agents."""
    return {
        "status": "success",
        "@context": "https://schema.org",
        "@type": "Dataset",
        "name": "Agent Pipeline Example Flow",
        "description": "Complete lead journey from cold prospect to customer",
        "example_flow": [
            {
                "stage": 1,
                "agent": "Discovery Agent",
                "input": "Cold lead from LinkedIn",
                "action": "Research company, find decision makers",
                "output": "Personalized outreach email",
                "success_metric": "Response rate > 15%",
            },
            {
                "stage": 2,
                "agent": "Qualification Agent",
                "input": "Lead responded to email",
                "action": "BANT scoring (Budget, Authority, Need, Timeline)",
                "output": "Qualification score 0-1",
                "success_metric": "Qualified leads > 0.7 score",
            },
            {
                "stage": 3,
                "agent": "Proposal Agent",
                "input": "Qualified lead with budget confirmed",
                "action": "Generate custom proposal with pricing options",
                "output": "Multi-tier proposal deck",
                "success_metric": "Proposal acceptance rate > 40%",
            },
            {
                "stage": 4,
                "agent": "Objection Handler",
                "input": "Prospect raises concerns",
                "action": "Auto-respond with case studies, testimonials",
                "output": "Objection resolution",
                "success_metric": "Objection conversion > 60%",
            },
            {
                "stage": 5,
                "agent": "Negotiation Agent",
                "input": "Price/terms discussion",
                "action": "Dynamic pricing within authority matrix",
                "output": "Final offer with contract",
                "success_metric": "Deal size retention > 90%",
            },
            {
                "stage": 6,
                "agent": "Closing Agent",
                "input": "Agreed terms",
                "action": "Send for signature, activate onboarding",
                "output": "Signed contract + onboarding started",
                "success_metric": "Close rate > 70%",
            },
            {
                "stage": 7,
                "agent": "CS/Retention Agent",
                "input": "New customer",
                "action": "Onboarding, success metrics, expansion monitoring",
                "output": "Active customer with NPS tracking",
                "success_metric": "NPS > 50, Retention > 95%",
            },
        ],
        "key_metrics": {
            "lead_to_close_avg_days": 14,
            "avg_deal_size_usd": 75000,
            "pipeline_stages": 7,
            "escalation_rate_pct": 15,
            "human_touch_points": "Escalation only (efficient autonomous flow)",
        },
    }
