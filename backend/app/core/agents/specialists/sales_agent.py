"""
Sales Agent — Master of sales methodologies, tactics, and playbooks.

Specialties:
- Sales methodologies (MEDDIC, Sandler, Consultative, Challenger Sale)
- Sales tactics (discovery, qualification, objection handling, closing)
- Sales scripts and playbooks
- Training materials and guidance
"""

import logging
from typing import Dict, List, Any, Tuple, Optional
from enum import Enum
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class SalesMethodology(str, Enum):
    """Sales methodologies and frameworks."""
    MEDDIC = "meddic"  # Metrics, Economic Buyer, Decision Criteria, Decision Process, Identify Pain, Champion
    SANDLER = "sandler"  # Bonding & Rapport, Up-Front Contracts, Pain, Budget, Decision Process, Non-Conclusion
    CONSULTATIVE = "consultative"  # Listen, understand, recommend, align
    CHALLENGER_SALE = "challenger_sale"  # Teach, tailor, take control
    SPIN_SELLING = "spin_selling"  # Situation, Problem, Implication, Need-Payoff
    CONCEPTUAL_SELLING = "conceptual_selling"  # Establish advances, gather information


class SalesStage(str, Enum):
    """Sales pipeline stages."""
    PROSPECTING = "prospecting"
    FIRST_CONTACT = "first_contact"
    DISCOVERY = "discovery"
    QUALIFICATION = "qualification"
    NEEDS_ANALYSIS = "needs_analysis"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSING = "closing"
    POST_SALE = "post_sale"


class ObjectionType(str, Enum):
    """Types of sales objections."""
    PRICE = "price"  # Too expensive
    COMPETITION = "competition"  # We prefer competitor
    TIMING = "timing"  # Not the right time
    AUTHORITY = "authority"  # Can't make decision
    IMPLEMENTATION = "implementation"  # Too much effort to implement
    PAIN = "pain"  # Problem not urgent enough
    PRODUCT = "product"  # Missing features


@dataclass
class SalesPlaybook:
    """Sales playbook entry."""
    name: str
    description: str
    use_case: str
    target_stage: str
    success_criteria: List[str]
    template: str
    tips: List[str]


class SalesAgent:
    """Expert in sales techniques and methodologies."""

    METHODOLOGIES = {
        SalesMethodology.MEDDIC: {
            "name": "MEDDIC",
            "description": "Enterprise sales framework focusing on key stakeholders and decision process",
            "creator": "Dick Dunkel",
            "best_for": "Enterprise B2B sales (long, complex cycles)",
            "stages": [
                ("Metrics", "Identify buyer's metrics for success"),
                ("Economic Buyer", "Find who controls budget"),
                ("Decision Criteria", "Understand what they evaluate"),
                ("Decision Process", "Map their buying process"),
                ("Identify Pain", "Uncover business problems"),
                ("Champion", "Develop internal advocate"),
            ],
            "cycle_time": "3-12 months",
            "deal_size": "$50K+",
            "questions": [
                "How will your organization measure success?",
                "Who controls the budget for this initiative?",
                "What are the evaluation criteria?",
                "What is your decision-making process?",
                "What problems are you trying to solve?",
                "Who can advocate for us internally?",
            ],
        },

        SalesMethodology.SANDLER: {
            "name": "Sandler Selling System",
            "description": "Consultative approach that treats sales as mutual problem-solving",
            "creator": "David Sandler",
            "best_for": "Mid-market and enterprise, relationship-based sales",
            "stages": [
                ("Bonding & Rapport", "Build trust and rapport"),
                ("Up-Front Contracts", "Set expectations for conversation"),
                ("Pain", "Uncover real problems (emotional)"),
                ("Budget", "Understand budget constraints"),
                ("Decision Process", "Clarify how they decide"),
                ("Non-Conclusion", "Present only if strong fit"),
            ],
            "cycle_time": "2-6 months",
            "deal_size": "$10K-$100K",
            "questions": [
                "What would happen if you don't solve this?",
                "What's your process for making decisions?",
                "What's your budget range?",
                "Who else needs to be involved?",
                "What's the timeline?",
            ],
        },

        SalesMethodology.CONSULTATIVE: {
            "name": "Consultative Selling",
            "description": "Focus on understanding customer needs and providing tailored solutions",
            "creator": "Industry Standard",
            "best_for": "Complex solutions, high-touch sales",
            "stages": [
                ("Listen", "Actively listen to customer needs"),
                ("Understand", "Deeply understand their business"),
                ("Recommend", "Recommend tailored solution"),
                ("Align", "Ensure solution aligns with goals"),
                ("Support", "Support implementation and success"),
            ],
            "cycle_time": "1-6 months",
            "deal_size": "$5K-$50K",
            "questions": [
                "Tell me about your current situation...",
                "What are your main challenges?",
                "What have you tried so far?",
                "What would success look like?",
                "What's preventing you from achieving that?",
            ],
        },

        SalesMethodology.CHALLENGER_SALE: {
            "name": "Challenger Sale",
            "description": "Seller teaches, tailors, and takes control of complex sales",
            "creator": "Matthew Dixon & Brent Adamson",
            "best_for": "Insight selling, consultative enterprise deals",
            "stages": [
                ("Teach", "Share valuable insight about buyer's industry"),
                ("Tailor", "Customize teaching for their situation"),
                ("Take Control", "Lead with conviction and perspective"),
                ("Resolve Concerns", "Address objections with insight"),
                ("Commit", "Get buyer commitment"),
            ],
            "cycle_time": "2-8 months",
            "deal_size": "$20K-$500K+",
            "questions": [
                "Have you considered X perspective?",
                "Here's how companies like you are thinking about this...",
                "What I'm hearing is... Is that right?",
                "Based on that, here's what I'd recommend...",
            ],
        },

        SalesMethodology.SPIN_SELLING: {
            "name": "SPIN Selling",
            "description": "Question-based approach to uncover buyer needs",
            "creator": "Neil Rackham",
            "best_for": "Complex B2B sales, consultative approach",
            "stages": [
                ("Situation", "Ask questions about current situation"),
                ("Problem", "Explore potential problems"),
                ("Implication", "Help buyer see problem implications"),
                ("Need-Payoff", "Get buyer to state benefit of solving"),
            ],
            "cycle_time": "1-6 months",
            "deal_size": "$10K-$100K+",
            "questions_by_type": {
                "Situation": "Can you walk me through your current process?",
                "Problem": "Do you have any difficulty with this?",
                "Implication": "If you didn't solve this, what would be the impact?",
                "Need-Payoff": "Would it be helpful if we could...?",
            },
        },

        SalesMethodology.CONCEPTUAL_SELLING: {
            "name": "Conceptual Selling",
            "description": "Focus on buyer's objectives and establishing mutual understanding",
            "creator": "Stephen Heiman & Diane Sanchez",
            "best_for": "Complex solutions, high-value deals",
            "stages": [
                ("Objective", "Establish mutual objective for conversation"),
                ("Advance", "Define specific advance for each call"),
                ("Gather Information", "Understand buyer's thinking"),
                ("Mutual Commitment", "Build shared understanding"),
            ],
            "cycle_time": "2-6 months",
            "deal_size": "$25K-$500K+",
            "questions": [
                "What would you like to get out of this conversation?",
                "What specific advance would be helpful?",
                "Tell me how you typically approach this...",
                "How does that fit with your overall strategy?",
            ],
        },
    }

    PLAYBOOKS = {
        "cold_outreach": SalesPlaybook(
            name="Cold Outreach Framework",
            description="Initial outreach to cold prospects",
            use_case="First contact with prospects who don't know you",
            target_stage="PROSPECTING",
            success_criteria=[
                "Response rate > 5%",
                "Meeting scheduled",
                "Discovery call booked"
            ],
            template="""
Hi [Name],

I noticed [specific insight about their company/role].

We work with [target companies] to [key benefit], which typically results in [quantified outcome].

Would it make sense to chat for 15 minutes to see if there's a fit?

[Signature]
            """,
            tips=[
                "Personalize with specific research about them",
                "Lead with value, not pitch",
                "Reference specific insight or trigger",
                "Keep initial message concise (2-3 sentences)",
                "Include clear call-to-action",
                "Follow up 3-7 days if no response",
            ]
        ),

        "discovery_call": SalesPlaybook(
            name="Discovery Call Framework",
            description="Structured discovery conversation with qualified lead",
            use_case="First conversation with interested prospect",
            target_stage="DISCOVERY",
            success_criteria=[
                "Understanding of prospect's main challenges",
                "Identified economic buyer",
                "Timeline established",
                "Next step scheduled"
            ],
            template="""
1. RAPPORT (5 min)
   - Warm greeting
   - Confirm time available
   - Build personal connection

2. OBJECTIVE (2 min)
   - State purpose of call
   - Outline agenda

3. DISCOVERY (25 min)
   - Current situation questions
   - Challenge/pain questions
   - Implication questions
   - Need-payoff questions

4. POSITIONING (5 min)
   - Briefly position solution
   - Check for fit

5. NEXT STEPS (3 min)
   - Define specific advance
   - Confirm timeline
   - Schedule follow-up
            """,
            tips=[
                "Listen 70%, talk 30%",
                "Take notes (shows engagement)",
                "Ask 'why' follow-up questions",
                "Identify specific pain and desired outcomes",
                "Find economic buyer early",
                "Establish realistic timeline",
            ]
        ),

        "objection_handling": SalesPlaybook(
            name="Objection Handling Framework",
            description="Structured approach to common sales objections",
            use_case="When prospect raises concerns",
            target_stage="NEGOTIATION",
            success_criteria=[
                "Objection addressed",
                "Trust maintained",
                "Deal moves forward"
            ],
            template="""
1. LISTEN
   - Let them finish completely
   - Don't interrupt

2. ACKNOWLEDGE
   - "I understand your concern about..."
   - Show you heard them

3. PROBE
   - Ask clarifying questions
   - Understand real objection (not surface)

4. RESPOND
   - Address actual concern (not assumed)
   - Use proof/social proof/case study

5. CONFIRM
   - "Does that address your concern?"
   - Get agreement to move forward
            """,
            tips=[
                "Most objections are really concerns",
                "Surface objection often not real objection",
                "Always probe to understand fully",
                "Use specific case studies as proof",
                "Never argue with prospect",
                "Reframe objection as valid point",
            ]
        ),

        "closing": SalesPlaybook(
            name="Closing Techniques",
            description="Ethical approaches to closing sales",
            use_case="Moving deal to signed agreement",
            target_stage="CLOSING",
            success_criteria=[
                "Agreement signed",
                "Payment terms confirmed",
                "Implementation plan agreed"
            ],
            template="""
1. TRIAL CLOSE
   - "Does this approach make sense?"
   - Gauge interest level

2. SUMMARY CLOSE
   - Recap what you've agreed on
   - Confirm all points align

3. ASSUMPTIVE CLOSE
   - "The next step is implementation on [date]"
   - Assume forward momentum

4. ALTERNATIVE CLOSE
   - "Would you prefer option A or B?"
   - Binary choice closes faster

5. DIRECT CLOSE
   - "Are you ready to move forward?"
   - Clear, simple ask
            """,
            tips=[
                "Ask for commitment clearly",
                "Silence after ask (let them respond)",
                "Don't oversell at close",
                "Address remaining concerns",
                "Get everything in writing",
                "Confirm next steps in detail",
            ]
        ),
    }

    OBJECTION_RESPONSES = {
        ObjectionType.PRICE: {
            "reframe": "Not about cost, it's about ROI and value",
            "questions": [
                "What specifically is your budget?",
                "Is price the only concern, or are there others?",
                "What would make this investment make sense?",
            ],
            "responses": [
                "We typically see ROI within [X months]. Does that timeline work?",
                "Most clients invest $X to save $Y annually.",
                "Let's look at your pain cost vs. our investment cost.",
            ],
        },

        ObjectionType.COMPETITION: {
            "reframe": "Learn what competitor offers",
            "questions": [
                "What do you like most about them?",
                "What concerns do you have about that solution?",
                "What would we need to match?",
            ],
            "responses": [
                "They're great at X, we're better at Y.",
                "Here's how we differ in these specific areas...",
                "Many clients chose us because...",
            ],
        },

        ObjectionType.TIMING: {
            "reframe": "Create urgency or adjust timeline",
            "questions": [
                "What would need to change for this to be a priority?",
                "When are you planning to solve this?",
                "What's the risk of waiting?",
            ],
            "responses": [
                "The cost of delay is typically [X]...",
                "Most customers wish they'd started sooner.",
                "Would a phased approach work better?",
            ],
        },

        ObjectionType.AUTHORITY: {
            "reframe": "Identify true decision maker",
            "questions": [
                "Who else should be in this conversation?",
                "How do decisions like this typically get made?",
                "What would help you champion this internally?",
            ],
            "responses": [
                "Let's involve [stakeholder] in the next discussion.",
                "Here's documentation that helps build internal cases.",
                "Would a formal proposal help with your review?",
            ],
        },

        ObjectionType.IMPLEMENTATION: {
            "reframe": "Break down implementation into manageable pieces",
            "questions": [
                "What's your biggest implementation concern?",
                "How much internal resource can you dedicate?",
                "Would a phased rollout ease concerns?",
            ],
            "responses": [
                "We provide implementation support including...",
                "Most clients take [X] to fully implement.",
                "Let's create a detailed implementation plan.",
            ],
        },

        ObjectionType.PAIN: {
            "reframe": "Increase pain perception",
            "questions": [
                "Tell me more about that challenge...",
                "What's the impact if you don't fix this?",
                "How is this affecting your team?",
            ],
            "responses": [
                "Many organizations face this and regret delay.",
                "Here's what happened with similar companies...",
                "The cost of status quo is typically...",
            ],
        },

        ObjectionType.PRODUCT: {
            "reframe": "Understand what's missing",
            "questions": [
                "Which features are most important to you?",
                "Can you give me specific examples?",
                "How critical is this capability?",
            ],
            "responses": [
                "We have a roadmap including [feature].",
                "Here's how other clients solve for this...",
                "Many customers achieve this with our API/integration.",
            ],
        },
    }

    @staticmethod
    def get_methodology(methodology: SalesMethodology) -> Dict[str, Any]:
        """Get detailed information about a sales methodology."""
        return SalesAgent.METHODOLOGIES.get(methodology, {})

    @staticmethod
    def recommend_methodology(
        deal_size: float,
        cycle_length_months: int,
        complexity: str,  # simple, medium, complex
    ) -> Dict[str, Any]:
        """Recommend best methodology based on deal characteristics."""
        recommendation = {
            "primary": None,
            "secondary": [],
            "rationale": "",
            "key_focuses": [],
        }

        # Scoring logic
        scores = {}
        for methodology_key, methodology in SalesAgent.METHODOLOGIES.items():
            score = 0

            # Deal size matching
            size_range = methodology.get("deal_size", "")
            if deal_size < 10000 and "$" in size_range and "K" in size_range:
                score += 20
            elif deal_size > 50000 and "50K" in size_range:
                score += 20

            # Complexity matching
            if complexity == "complex" and methodology_key in [
                SalesMethodology.MEDDIC,
                SalesMethodology.CHALLENGER_SALE
            ]:
                score += 30

            # Cycle time matching
            cycle_range = methodology.get("cycle_time", "")
            if cycle_length_months > 3 and "6" in cycle_range:
                score += 20

            scores[methodology_key] = score

        # Sort by score
        sorted_methodologies = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        if sorted_methodologies:
            primary_key = sorted_methodologies[0][0]
            recommendation["primary"] = {
                "methodology": SalesAgent.METHODOLOGIES[primary_key]["name"],
                "key": primary_key,
                "description": SalesAgent.METHODOLOGIES[primary_key]["description"],
            }

            for method_key, score in sorted_methodologies[1:4]:
                recommendation["secondary"].append({
                    "methodology": SalesAgent.METHODOLOGIES[method_key]["name"],
                    "key": method_key,
                })

        return recommendation

    @staticmethod
    def get_stage_guidance(stage: SalesStage) -> Dict[str, Any]:
        """Get guidance for a specific sales stage."""
        stage_guidance = {
            SalesStage.PROSPECTING: {
                "goal": "Identify ideal prospects",
                "tactics": [
                    "Research target accounts",
                    "Build contact list",
                    "Personalize outreach",
                    "Set outreach cadence"
                ],
                "success_metric": "Response rate > 5%",
                "duration": "Ongoing",
            },
            SalesStage.FIRST_CONTACT: {
                "goal": "Establish interest",
                "tactics": [
                    "Personalized email/outreach",
                    "Cold call with research",
                    "Referral introduction",
                    "Warm handoff"
                ],
                "success_metric": "Meeting scheduled",
                "duration": "1-2 weeks",
            },
            SalesStage.DISCOVERY: {
                "goal": "Understand needs deeply",
                "tactics": [
                    "Active listening",
                    "Problem questioning",
                    "Timeline exploration",
                    "Stakeholder mapping"
                ],
                "success_metric": "Clear pain identified",
                "duration": "1-2 weeks",
            },
            SalesStage.QUALIFICATION: {
                "goal": "Confirm fit and budget",
                "tactics": [
                    "Budget confirmation",
                    "Authority mapping",
                    "Priority assessment",
                    "Timeline clarification"
                ],
                "success_metric": "Lead qualified for proposal",
                "duration": "1 week",
            },
            SalesStage.NEEDS_ANALYSIS: {
                "goal": "Detail solution approach",
                "tactics": [
                    "Deep dive meetings",
                    "Requirements gathering",
                    "Technical assessment",
                    "ROI calculation"
                ],
                "success_metric": "Detailed requirements doc",
                "duration": "2-4 weeks",
            },
            SalesStage.PROPOSAL: {
                "goal": "Present tailored solution",
                "tactics": [
                    "Custom proposal creation",
                    "Presentation preparation",
                    "Proposal walkthrough",
                    "Q&A preparation"
                ],
                "success_metric": "Proposal accepted for review",
                "duration": "1-2 weeks",
            },
            SalesStage.NEGOTIATION: {
                "goal": "Resolve objections and concerns",
                "tactics": [
                    "Terms negotiation",
                    "Objection handling",
                    "Approval process support",
                    "Stakeholder management"
                ],
                "success_metric": "Agreement in principle",
                "duration": "2-4 weeks",
            },
            SalesStage.CLOSING: {
                "goal": "Get signed agreement",
                "tactics": [
                    "Trial closes",
                    "Contract negotiation",
                    "Signature collection",
                    "Kickoff scheduling"
                ],
                "success_metric": "Contract signed",
                "duration": "1-2 weeks",
            },
            SalesStage.POST_SALE: {
                "goal": "Ensure customer success",
                "tactics": [
                    "Implementation planning",
                    "Onboarding support",
                    "Value realization",
                    "Expansion planning"
                ],
                "success_metric": "Customer onboarded",
                "duration": "Ongoing",
            },
        }

        return stage_guidance.get(stage, {})

    @staticmethod
    def handle_objection(
        objection_type: ObjectionType,
        specific_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get structured response to objection."""
        objection_response = SalesAgent.OBJECTION_RESPONSES.get(objection_type, {})

        return {
            "objection_type": objection_type.value,
            "reframe": objection_response.get("reframe"),
            "probe_questions": objection_response.get("questions", []),
            "response_options": objection_response.get("responses", []),
            "context_note": specific_context,
        }

    @staticmethod
    def get_playbook(playbook_key: str) -> Optional[SalesPlaybook]:
        """Get sales playbook."""
        return SalesAgent.PLAYBOOKS.get(playbook_key)

    @staticmethod
    def create_sales_script(
        scenario: str,
        prospect_context: Dict[str, Any],
        methodology: Optional[SalesMethodology] = None
    ) -> Dict[str, Any]:
        """Create customized sales script."""
        script_structure = {
            "scenario": scenario,
            "opening": "",
            "discovery": [],
            "positioning": "",
            "handling_objections": [],
            "closing": [],
            "follow_up": "",
            "tips": [],
        }

        if scenario == "cold_call":
            script_structure["opening"] = (
                f"Hi {prospect_context.get('first_name', '[Name]')}, "
                f"this is [Your Name] from [Company]. "
                f"I noticed [specific insight], and I thought it might be worth a quick conversation. "
                f"Do you have a few minutes?"
            )
            script_structure["tips"] = [
                "Personalize with research",
                "Lead with insight, not pitch",
                "Get permission before continuing",
                "Be prepared for 'call back later'",
            ]

        elif scenario == "discovery":
            script_structure["discovery"] = [
                "Tell me about your current situation with [topic]...",
                "What challenges are you facing?",
                "What have you tried so far?",
                "What would success look like?",
                "What's preventing you from achieving that?",
            ]

        return script_structure

    @staticmethod
    def create_training_material(topic: str) -> Dict[str, Any]:
        """Create sales training material."""
        return {
            "topic": topic,
            "learning_objectives": [],
            "key_concepts": [],
            "practice_scenarios": [],
            "role_play_exercises": [],
            "assessment": [],
            "recommended_reading": [],
        }
