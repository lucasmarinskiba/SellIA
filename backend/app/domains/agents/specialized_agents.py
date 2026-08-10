"""Specialized sales agents for different pipeline stages."""

from typing import Dict, Any
import asyncio
from datetime import datetime

from app.domains.agents.base_agent import (
    SalesAgent,
    AgentType,
    AgentContext,
    AgentDecision,
)


class DiscoveryAgent(SalesAgent):
    """Handles initial lead research and outreach."""

    agent_type = AgentType.DISCOVERY
    name = "Discovery Agent"
    description = "Research leads, identify pain points, schedule initial calls"

    async def evaluate(self, context: AgentContext) -> bool:
        """Suitable for new/cold leads with minimal interaction history."""
        return (
            context.current_stage == "lead_source"
            and context.intent_score >= 0.5
            and len(context.interaction_history) < 2
        )

    async def execute(self, context: AgentContext) -> AgentDecision:
        """Research company, find decision makers, prepare outreach."""
        await asyncio.sleep(0.1)  # Simulate research

        decision = AgentDecision(
            next_agent=AgentType.QUALIFICATION,
            action="send_personalized_research_email",
            confidence=0.85,
            reasoning="Lead shows interest, ready for personalized outreach",
            data={
                "email_template": "discovery_outreach",
                "research_depth": "comprehensive",
                "decision_makers_identified": 2,
                "suggested_call_time": "next_business_day",
            },
        )
        self.record_execution(True, 100)
        return decision


class QualificationAgent(SalesAgent):
    """Validates fit, budget, timeline using BANT framework."""

    agent_type = AgentType.QUALIFICATION
    name = "Qualification Agent"
    description = "BANT scoring, objection pre-handling, deal sizing"

    async def evaluate(self, context: AgentContext) -> bool:
        """Suitable after initial engagement."""
        return (
            context.current_stage in ["discovery", "qualification"]
            and len(context.interaction_history) >= 2
            and context.intent_score >= 0.6
        )

    async def execute(self, context: AgentContext) -> AgentDecision:
        """Score lead using BANT, determine next action."""
        await asyncio.sleep(0.1)  # Simulate qualification logic

        # Simulate BANT scoring
        budget_score = 0.8 if context.budget else 0.4
        authority_score = 0.75 if context.decision_makers else 0.3
        need_score = context.intent_score
        timeline_score = 0.9 if context.timeline else 0.5

        bant_score = (budget_score + authority_score + need_score + timeline_score) / 4

        next_agent = (
            AgentType.PROPOSAL
            if bant_score >= 0.7
            else AgentType.OBJECTION_HANDLING
        )

        decision = AgentDecision(
            next_agent=next_agent,
            action="qualify_lead_bant" if bant_score >= 0.7 else "handle_objection",
            confidence=bant_score,
            reasoning=f"BANT score: {bant_score:.2f}. {'Qualified to proposal' if bant_score >= 0.7 else 'Needs objection handling'}",
            data={
                "bant_score": bant_score,
                "budget_score": budget_score,
                "authority_score": authority_score,
                "need_score": need_score,
                "timeline_score": timeline_score,
                "recommended_deal_size": context.expected_deal_size,
            },
        )
        self.record_execution(bant_score >= 0.7, 150)
        return decision


class ProposalAgent(SalesAgent):
    """Generates customized proposals with product-fit and pricing."""

    agent_type = AgentType.PROPOSAL
    name = "Proposal Agent"
    description = "Generate custom decks, pricing options, ROI calculations"

    async def evaluate(self, context: AgentContext) -> bool:
        """Suitable for qualified leads."""
        return (
            context.current_stage in ["qualification", "proposal"]
            and context.close_probability >= 0.6
        )

    async def execute(self, context: AgentContext) -> AgentDecision:
        """Generate proposal with customization and pricing."""
        await asyncio.sleep(0.2)  # Simulate proposal generation

        decision = AgentDecision(
            next_agent=AgentType.OBJECTION_HANDLING,
            action="send_proposal_deck",
            confidence=0.88,
            reasoning="Qualified lead ready for proposal. Multi-option pricing included.",
            data={
                "proposal_type": "enterprise_custom",
                "pricing_tiers": [
                    {"name": "Standard", "price": "$50k/year"},
                    {"name": "Professional", "price": "$75k/year"},
                    {"name": "Enterprise", "price": "$120k/year"},
                ],
                "roi_projection_months": 6,
                "includes_pilot": True,
                "discount_authority": 15,
            },
        )
        self.record_execution(True, 200)
        return decision


class ObjectionHandlingAgent(SalesAgent):
    """Addresses objections with social proof and technical expertise."""

    agent_type = AgentType.OBJECTION_HANDLING
    name = "Objection Handling Agent"
    description = "FAQ database, case studies, expert escalation"

    async def evaluate(self, context: AgentContext) -> bool:
        """Suitable when objections detected or confidence drops."""
        return context.current_stage in ["qualification", "proposal", "objection"]

    async def execute(self, context: AgentContext) -> AgentDecision:
        """Route objection to appropriate rebuttal or expert."""
        await asyncio.sleep(0.15)  # Simulate objection analysis

        # Simulate objection routing
        decision = AgentDecision(
            next_agent=AgentType.NEGOTIATION,
            action="send_case_study_and_testimonial",
            confidence=0.82,
            reasoning="Objection identified and addressed with social proof.",
            data={
                "objection_type": "price_concern",
                "relevant_case_studies": 3,
                "testimonials_included": 2,
                "expert_ready": True,
                "escalation_threshold": 2,
            },
        )
        self.record_execution(True, 120)
        return decision


class NegotiationAgent(SalesAgent):
    """Handles price/terms negotiation with authority matrix."""

    agent_type = AgentType.NEGOTIATION
    name = "Negotiation Agent"
    description = "Dynamic pricing, term flexibility, contract automation"

    async def evaluate(self, context: AgentContext) -> bool:
        """Suitable when discussing terms."""
        return context.current_stage in ["proposal", "negotiation"]

    async def execute(self, context: AgentContext) -> AgentDecision:
        """Negotiate terms within authority limits."""
        await asyncio.sleep(0.1)

        decision = AgentDecision(
            next_agent=AgentType.CLOSING,
            action="send_final_offer",
            confidence=0.9,
            reasoning="Terms negotiated within discount authority. Ready for closing.",
            data={
                "final_price": context.expected_deal_size * 0.95,
                "payment_terms": "net_30",
                "contract_type": "standard_msa",
                "legal_review_needed": False,
            },
        )
        self.record_execution(True, 100)
        return decision


class ClosingAgent(SalesAgent):
    """Automates signature and handoff to success."""

    agent_type = AgentType.CLOSING
    name = "Closing Agent"
    description = "Signature automation, success path activation"

    async def evaluate(self, context: AgentContext) -> bool:
        """Suitable when ready to close."""
        return context.current_stage == "negotiation" and context.close_probability >= 0.8

    async def execute(self, context: AgentContext) -> AgentDecision:
        """Send for signature and trigger onboarding."""
        await asyncio.sleep(0.15)

        decision = AgentDecision(
            next_agent=AgentType.CS_RETENTION,
            action="send_for_signature_and_onboard",
            confidence=0.95,
            reasoning="Terms accepted. Contract ready. Onboarding path activated.",
            data={
                "docusign_template": "standard_msa",
                "onboarding_start_date": "next_week",
                "csm_assignment": "auto",
                "success_metrics_dashboard": "activated",
            },
        )
        self.record_execution(True, 150)
        return decision


class CSRetentionAgent(SalesAgent):
    """Customer success, onboarding, upsell, and churn prevention."""

    agent_type = AgentType.CS_RETENTION
    name = "CS/Retention Agent"
    description = "Onboarding, upsell triggers, churn prevention"

    async def evaluate(self, context: AgentContext) -> bool:
        """Suitable for closed deals and existing customers."""
        return context.current_stage in ["closing", "customer"]

    async def execute(self, context: AgentContext) -> AgentDecision:
        """Initiate onboarding and monitor for expansion."""
        await asyncio.sleep(0.15)

        decision = AgentDecision(
            next_agent=None,
            action="activate_onboarding_and_monitor",
            confidence=0.93,
            reasoning="Customer onboarded. Monitoring for expansion and churn risks.",
            data={
                "onboarding_program": "enterprise_90day",
                "success_metrics": [
                    "feature_adoption",
                    "active_users",
                    "nps_score",
                ],
                "upsell_triggers": ["expansion_threshold_80pct", "nps_score_gt_8"],
                "churn_watch_signals": [
                    "inactivity_30days",
                    "support_ticket_spike",
                ],
                "renewal_months_out": 11,
            },
        )
        self.record_execution(True, 180)
        return decision


# Agent registry
AGENT_REGISTRY = {
    AgentType.DISCOVERY: DiscoveryAgent(),
    AgentType.QUALIFICATION: QualificationAgent(),
    AgentType.PROPOSAL: ProposalAgent(),
    AgentType.OBJECTION_HANDLING: ObjectionHandlingAgent(),
    AgentType.NEGOTIATION: NegotiationAgent(),
    AgentType.CLOSING: ClosingAgent(),
    AgentType.CS_RETENTION: CSRetentionAgent(),
}
